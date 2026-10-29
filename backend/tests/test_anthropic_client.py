"""The Claude client, tested against a fake SDK (no network, no API key)."""

import json
from types import SimpleNamespace

import pytest

from jobfit.config import Settings
from jobfit.llm.anthropic_client import AnthropicClient
from jobfit.llm.base import LLMError
from jobfit.schemas import Requirement

EXTRACTION_JSON = json.dumps(
    {
        "job_title": "Data Analyst",
        "company": "Acme",
        "requirements": [
            {"id": "R1", "text": "SQL", "importance": "must_have", "category": "skill", "keywords": ["SQL"]}
        ],
        "work_rights": {"status": "not_mentioned", "detail": "", "quote": ""},
    }
)


class FakeMessages:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def fake_sdk(text=EXTRACTION_JSON, stop_reason="end_turn", error=None):
    content = [SimpleNamespace(type="thinking", thinking="..."), SimpleNamespace(type="text", text=text)]
    messages = FakeMessages(SimpleNamespace(stop_reason=stop_reason, content=content), error)
    return SimpleNamespace(messages=messages)


SETTINGS = Settings(provider="anthropic", anthropic_api_key="test")


def test_request_shape_for_extraction():
    sdk = fake_sdk()
    client = AnthropicClient(SETTINGS, sdk_client=sdk)
    result = client.extract_requirements("We need SQL.", "zh")

    assert result.requirements[0].keywords == ["SQL"]
    call = sdk.messages.calls[0]
    assert call["model"] == client.extract_model == AnthropicClient.DEFAULT_EXTRACT_MODEL
    assert call["output_config"]["effort"] == SETTINGS.extract_effort
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert call["output_config"]["format"]["schema"]["additionalProperties"] is False
    assert "Simplified Chinese" in call["system"]
    assert "<job_description>\nWe need SQL.\n</job_description>" in call["messages"][0]["content"]
    # API version 2026-10-21 rejects sampling parameters.
    assert not {"temperature", "top_p", "top_k"} & call.keys()


def test_match_uses_the_match_model():
    match_json = json.dumps({"matches": [], "suggestions": [], "summary": "ok"})
    sdk = fake_sdk(text=match_json)
    requirement = Requirement(id="R1", text="SQL", importance="must_have", category="skill", keywords=["SQL"])
    client = AnthropicClient(SETTINGS, sdk_client=sdk)
    result = client.match_resume([requirement], "resume text", "en")

    assert result.summary == "ok"
    call = sdk.messages.calls[0]
    assert call["model"] == AnthropicClient.DEFAULT_MATCH_MODEL
    assert call["output_config"]["effort"] == SETTINGS.match_effort
    assert "<resume>\nresume text\n</resume>" in call["messages"][0]["content"]


@pytest.mark.parametrize(
    "sdk, code",
    [
        (fake_sdk(stop_reason="refusal"), "ai_refused"),
        (fake_sdk(stop_reason="max_tokens"), "ai_output_too_long"),
        (fake_sdk(text="not json"), "ai_bad_output"),
        (fake_sdk(text=""), "ai_bad_output"),
        (fake_sdk(error=RuntimeError("connection reset")), "ai_unavailable"),
    ],
)
def test_failures_become_user_facing_errors(sdk, code):
    with pytest.raises(LLMError) as info:
        AnthropicClient(SETTINGS, sdk_client=sdk).extract_requirements("We need SQL.", "en")
    assert info.value.code == code


def test_missing_api_key_is_reported():
    with pytest.raises(LLMError) as info:
        AnthropicClient(Settings(provider="anthropic", anthropic_api_key=None))
    assert info.value.code == "ai_not_configured"


def test_model_names_can_be_overridden():
    sdk = fake_sdk()
    settings = Settings(provider="anthropic", anthropic_api_key="test", extract_model="claude-opus-5-5")
    AnthropicClient(settings, sdk_client=sdk).extract_requirements("We need SQL.", "en")
    assert sdk.messages.calls[0]["model"] == "claude-opus-5-5"


def test_token_usage_is_counted():
    sdk = fake_sdk()
    sdk.messages.response.usage = SimpleNamespace(input_tokens=900, output_tokens=400)
    client = AnthropicClient(SETTINGS, sdk_client=sdk)
    client.extract_requirements("We need SQL.", "en")
    totals = client.usage.snapshot()
    assert (totals.calls, totals.input_tokens, totals.output_tokens) == (1, 900, 400)
