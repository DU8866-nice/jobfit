"""Claude via the Anthropic Python SDK (v2, API version 2026-10-21).

Each step is one Messages API call with a JSON schema in `output_config.format`,
so the reply is guaranteed to parse into the Pydantic model. `output_config.effort`
trades depth of thinking for speed and cost per step.
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ..config import Settings
from ..prompts import build_extract_user, build_match_user, extract_system, match_system
from ..schemas import ExtractionResult, Language, MatchResult, Requirement
from .base import LLMError, UsageMeter
from .json_schema import strict_json_schema

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

EXTRACT_MAX_TOKENS = 8_000
# max_tokens covers thinking as well as the answer, so leave room for both.
MATCH_MAX_TOKENS = 16_000


class AnthropicClient:
    name = "anthropic"
    # Requirement extraction is a simple task, so it uses a fast, cheap model.
    DEFAULT_EXTRACT_MODEL = "claude-haiku-5-5"
    # Matching needs careful reading of two documents, so it uses a stronger model.
    DEFAULT_MATCH_MODEL = "claude-sonnet-5-5"

    def __init__(self, settings: Settings, sdk_client: Any | None = None) -> None:
        """`sdk_client` lets tests pass a fake in place of `anthropic.Anthropic`."""
        if sdk_client is None:
            if not settings.anthropic_api_key:
                raise LLMError("ai_not_configured", "ANTHROPIC_API_KEY is not set.")
            try:
                import anthropic
            except ImportError as exc:
                raise LLMError("ai_not_configured", "The anthropic package is not installed.") from exc
            sdk_client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key, max_retries=2, timeout=120.0
            )
        self._sdk = sdk_client
        self._settings = settings
        self.extract_model = settings.extract_model or self.DEFAULT_EXTRACT_MODEL
        self.match_model = settings.match_model or self.DEFAULT_MATCH_MODEL
        self.usage = UsageMeter()

    def extract_requirements(self, job_description: str, language: Language) -> ExtractionResult:
        return self._structured(
            model=self.extract_model,
            effort=self._settings.extract_effort,
            max_tokens=EXTRACT_MAX_TOKENS,
            system=extract_system(language),
            user=build_extract_user(job_description),
            output_type=ExtractionResult,
        )

    def match_resume(
        self, requirements: list[Requirement], resume_text: str, language: Language
    ) -> MatchResult:
        return self._structured(
            model=self.match_model,
            effort=self._settings.match_effort,
            max_tokens=MATCH_MAX_TOKENS,
            system=match_system(language),
            user=build_match_user(requirements, resume_text),
            output_type=MatchResult,
        )

    def _structured(
        self,
        *,
        model: str,
        effort: str,
        max_tokens: int,
        system: str,
        user: str,
        output_type: type[T],
    ) -> T:
        try:
            response = self._sdk.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={
                    "effort": effort,
                    "format": {"type": "json_schema", "schema": strict_json_schema(output_type)},
                },
            )
        except Exception as exc:  # the SDK's errors all derive from anthropic.APIError
            log.exception("Claude request failed")
            raise LLMError("ai_unavailable", "The AI service could not be reached. Please try again in a minute.") from exc

        usage = getattr(response, "usage", None)
        self.usage.add(getattr(usage, "input_tokens", None), getattr(usage, "output_tokens", None))

        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason == "refusal":
            raise LLMError("ai_refused", "The AI declined to analyse this input.")
        if stop_reason == "max_tokens":
            raise LLMError(
                "ai_output_too_long", "The input was too long to analyse in one go. Try a shorter job description or resume."
            )

        text = next(
            (block.text for block in response.content if getattr(block, "type", None) == "text"),
            None,
        )
        if not text:
            raise LLMError("ai_bad_output", "The AI returned an empty answer. Please try again.")
        try:
            return output_type.model_validate_json(text)
        except ValidationError as exc:
            log.warning("Structured output failed validation: %s", exc)
            raise LLMError("ai_bad_output", "The AI returned an answer in an unexpected format. Please try again.") from exc
