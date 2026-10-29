"""DeepSeek through its OpenAI-compatible Chat Completions API.

DeepSeek's JSON mode (`response_format={"type": "json_object"}`) guarantees valid
JSON but not our schema, and it occasionally returns empty content. So:

* the JSON Schema is written into the system prompt (JSON mode also requires the
  word "json" to appear in the prompt);
* the reply is validated with Pydantic;
* if it is empty or doesn't fit the schema, we ask once more, quoting the
  validation error, before giving up.

The evidence checks in the pipeline apply to this provider exactly as to Claude.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ..config import Settings
from ..prompts import build_extract_user, build_match_user, extract_system, match_system
from ..schemas import ExtractionResult, Language, MatchResult, Requirement
from .base import LLMError
from .json_schema import strict_json_schema

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_TOKENS = 8_000
MAX_ATTEMPTS = 2


def _with_schema(system: str, output_type: type[BaseModel]) -> str:
    schema = json.dumps(strict_json_schema(output_type), ensure_ascii=False)
    return (
        f"{system}\n"
        "Reply with one JSON object and nothing else. It must match this JSON Schema exactly, "
        "with every field present:\n"
        f"<json_schema>\n{schema}\n</json_schema>"
    )


class DeepSeekClient:
    name = "deepseek"
    DEFAULT_EXTRACT_MODEL = "deepseek-flash"
    DEFAULT_MATCH_MODEL = "deepseek-flash"

    def __init__(self, settings: Settings, sdk_client: Any | None = None) -> None:
        """`sdk_client` lets tests pass a fake in place of `openai.OpenAI`."""
        if sdk_client is None:
            if not settings.deepseek_api_key:
                raise LLMError("ai_not_configured", "DEEPSEEK_API_KEY is not set.")
            try:
                import openai
            except ImportError as exc:
                raise LLMError("ai_not_configured", "The openai package is not installed.") from exc
            sdk_client = openai.OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                max_retries=2,
                timeout=120.0,
            )
        self._sdk = sdk_client
        self.extract_model = settings.extract_model or self.DEFAULT_EXTRACT_MODEL
        self.match_model = settings.match_model or self.DEFAULT_MATCH_MODEL

    def extract_requirements(self, job_description: str, language: Language) -> ExtractionResult:
        return self._structured(
            model=self.extract_model,
            system=extract_system(language),
            user=build_extract_user(job_description),
            output_type=ExtractionResult,
        )

    def match_resume(
        self, requirements: list[Requirement], resume_text: str, language: Language
    ) -> MatchResult:
        return self._structured(
            model=self.match_model,
            system=match_system(language),
            user=build_match_user(requirements, resume_text),
            output_type=MatchResult,
        )

    def _structured(self, *, model: str, system: str, user: str, output_type: type[T]) -> T:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": _with_schema(system, output_type)},
            {"role": "user", "content": user},
        ]
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self._sdk.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    max_tokens=MAX_TOKENS,
                )
            except Exception as exc:  # the SDK's errors all derive from openai.APIError
                log.exception("DeepSeek request failed")
                raise LLMError(
                    "ai_unavailable", "The AI service could not be reached. Please try again in a minute."
                ) from exc

            choice = response.choices[0]
            if choice.finish_reason == "length":
                raise LLMError(
                    "ai_output_too_long",
                    "The input was too long to analyse in one go. Try a shorter job description or resume.",
                )
            if choice.finish_reason == "content_filter":
                raise LLMError("ai_refused", "The AI declined to analyse this input.")

            content = (choice.message.content or "").strip()
            if not content:
                log.warning("DeepSeek returned empty content (attempt %d)", attempt)
                continue
            try:
                return output_type.model_validate_json(content)
            except ValidationError as exc:
                log.warning("DeepSeek output failed validation (attempt %d): %s", attempt, exc)
                messages = messages[:2] + [
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": (
                            "That JSON does not match the schema. Problems:\n"
                            f"{exc.errors(include_url=False, include_input=False)}\n"
                            "Reply again with the corrected JSON object only."
                        ),
                    },
                ]

        raise LLMError("ai_bad_output", "The AI returned an answer in an unexpected format. Please try again.")
