from __future__ import annotations

from typing import Protocol

from ..errors import AppError
from ..schemas import ExtractionResult, Language, MatchResult, Requirement


class LLMError(AppError):
    """The model call failed."""


class LLMClient(Protocol):
    name: str

    def extract_requirements(self, job_description: str, language: Language) -> ExtractionResult: ...

    def match_resume(
        self, requirements: list[Requirement], resume_text: str, language: Language
    ) -> MatchResult: ...
