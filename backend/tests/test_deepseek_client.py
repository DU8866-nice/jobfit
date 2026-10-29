"""The DeepSeek client, tested against a fake OpenAI-compatible SDK (no network, no API key)."""

import json
from types import SimpleNamespace

import pytest

from jobfit.config import Settings
from jobfit.llm.base import LLMError
from jobfit.llm.deepseek_client import DeepSeekClient

GOOD = json.dumps(
    {
        "job_title": "Data Analyst",
        "company": "",
        "requirements": [
            {"id": "R1", "text": "SQL", "importance": "must_have", "category": "skill", "keywords": ["SQL"]}
        ],
        "work_rights": {"status": "not_mentioned", "detail": "", "quote": ""},
    }
)
MISSING_FIELD = json.dumps({"job_title": "Data Analyst", "requirements": []})


def reply(content, finish_reason="stop"):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(content=content))])


class FakeCompletions:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def fake_sdk(*replies):
    completions = FakeCompletions(replies)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions


SETTINGS = Settings(provider="deepseek", deepseek_api_key="test")


def test_request_uses_json_mode_and_puts_the_schema_in_the_prompt():
    sdk, completions = fake_sdk(reply(GOOD))
    result = DeepSeekClient(SETTINGS, sdk_client=sdk).extract_requirements("We need SQL.", "en")

    assert result.requirements[0].text == "SQL"
    call = completions.calls[0]
    assert call["model"] == DeepSeekClient.DEFAULT_EXTRACT_MODEL
    assert call["response_format"] == {"type": "json_object"}
    system = call["messages"][0]["content"]
    assert "JSON" in system and "<json_schema>" in system, "JSON mode needs the word json and the schema"
    assert call["messages"][1]["content"].startswith("<job_description>")


def test_retries_once_with_the_validation_error():
    sdk, completions = fake_sdk(reply(MISSING_FIELD), reply(GOOD))
    result = DeepSeekClient(SETTINGS, sdk_client=sdk).extract_requirements("We need SQL.", "en")

    assert result.job_title == "Data Analyst"
    assert len(completions.calls) == 2
    retry_messages = completions.calls[1]["messages"]
    assert retry_messages[2] == {"role": "assistant", "content": MISSING_FIELD}
    assert "does not match the schema" in retry_messages[3]["content"]


def test_retries_once_after_empty_content():
    sdk, completions = fake_sdk(reply(""), reply(GOOD))
    DeepSeekClient(SETTINGS, sdk_client=sdk).extract_requirements("We need SQL.", "en")
    assert len(completions.calls) == 2


def test_gives_up_after_two_bad_replies():
    sdk, _ = fake_sdk(reply(MISSING_FIELD), reply("{}"))
    with pytest.raises(LLMError) as info:
        DeepSeekClient(SETTINGS, sdk_client=sdk).extract_requirements("We need SQL.", "en")
    assert info.value.code == "ai_bad_output"


@pytest.mark.parametrize(
    "item, code",
    [
        (reply(GOOD, finish_reason="length"), "ai_output_too_long"),
        (reply("", finish_reason="content_filter"), "ai_refused"),
        (RuntimeError("connection reset"), "ai_unavailable"),
    ],
)
def test_failures_become_user_facing_errors(item, code):
    sdk, _ = fake_sdk(item)
    with pytest.raises(LLMError) as info:
        DeepSeekClient(SETTINGS, sdk_client=sdk).extract_requirements("We need SQL.", "en")
    assert info.value.code == code


def test_missing_api_key_is_reported():
    with pytest.raises(LLMError) as info:
        DeepSeekClient(Settings(provider="deepseek"))
    assert info.value.code == "ai_not_configured"
