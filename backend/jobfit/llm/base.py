from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Protocol

from ..errors import AppError
from ..schemas import ExtractionResult, Language, MatchResult, Requirement


class LLMError(AppError):
    """The model call failed."""


@dataclass(frozen=True)
class UsageTotals:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def __sub__(self, other: UsageTotals) -> UsageTotals:
        return UsageTotals(
            self.calls - other.calls,
            self.input_tokens - other.input_tokens,
            self.output_tokens - other.output_tokens,
        )


class UsageMeter:
    """Running token totals for one client. Fixed size, so it is safe in a long-running server."""

    def __init__(self) -> None:
        self._totals = UsageTotals()
        self._lock = threading.Lock()

    def add(self, input_tokens: int | None, output_tokens: int | None) -> None:
        with self._lock:
            t = self._totals
            self._totals = UsageTotals(t.calls + 1, t.input_tokens + (input_tokens or 0), t.output_tokens + (output_tokens or 0))

    def snapshot(self) -> UsageTotals:
        with self._lock:
            return self._totals


class LLMClient(Protocol):
    name: str

    def extract_requirements(self, job_description: str, language: Language) -> ExtractionResult: ...

    def match_resume(
        self, requirements: list[Requirement], resume_text: str, language: Language
    ) -> MatchResult: ...
