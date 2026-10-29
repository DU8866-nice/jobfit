"""Data shapes.

Two groups:

* LLM-facing models (ExtractionResult, MatchResult): the JSON schemas the model must
  fill in. Every field is required and has no default, because structured outputs
  limit the number of optional fields and a required field is never silently skipped.
* API-facing models (AnalysisResult and friends): what the backend returns after it
  has checked the model's answer against the source documents.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Language = Literal["en", "zh"]
Importance = Literal["must_have", "nice_to_have"]
Category = Literal["skill", "experience", "education", "certification", "other"]
MatchStatus = Literal["met", "partial", "missing"]
WorkRightsStatus = Literal["not_mentioned", "required", "preferred"]
# Why the backend changed or filled in a requirement's status. The UI shows these in the user's language.
ReportNote = Literal["not_assessed", "evidence_not_found"]


# ---------------------------------------------------------------- LLM-facing


class Requirement(BaseModel):
    id: str = Field(description="Short id: R1, R2, R3 ...")
    text: str = Field(description="One requirement, paraphrased in under 20 words")
    importance: Importance = Field(
        description="must_have unless the ad marks it as preferred, desirable, a bonus or nice to have"
    )
    category: Category
    keywords: list[str] = Field(
        description=(
            "Exact terms from the job ad that a recruiter or applicant tracking system would scan for, "
            "such as 'Power BI' or 'stakeholder management'. Empty list if none."
        )
    )


class WorkRights(BaseModel):
    status: WorkRightsStatus = Field(
        description="Whether the ad asks for citizenship, permanent residency, full working rights or a security clearance"
    )
    detail: str = Field(
        description="Plain-English summary such as 'Citizenship required for a government security clearance'. Empty if not mentioned."
    )
    quote: str = Field(
        description="The sentence from the job ad that states it, copied exactly. Empty if not mentioned."
    )


class ExtractionResult(BaseModel):
    job_title: str
    company: str = Field(description="Company name, or an empty string if the ad does not say")
    requirements: list[Requirement]
    work_rights: WorkRights


class RequirementMatch(BaseModel):
    requirement_id: str
    status: MatchStatus
    evidence: list[str] = Field(
        description="Up to 2 short quotes copied character-for-character from the resume. Empty when status is missing."
    )
    explanation: str = Field(description="One sentence explaining the status")


class Suggestion(BaseModel):
    requirement_ids: list[str] = Field(description="Ids of the requirements this edit helps with")
    original: str = Field(description="One line copied character-for-character from the resume")
    rewrite: str = Field(
        description="The improved line. May only reword, reorder or add [placeholders]; never add new facts."
    )
    rationale: str = Field(description="One sentence on why this edit helps for this job")


class MatchResult(BaseModel):
    matches: list[RequirementMatch]
    suggestions: list[Suggestion]
    summary: str = Field(description="Two or three plain sentences on overall fit, without flattery")


# ---------------------------------------------------------------- API-facing


class RequirementReport(BaseModel):
    id: str
    text: str
    importance: Importance
    category: Category
    keywords: list[str]
    status: MatchStatus
    evidence: list[str]
    explanation: str
    note: ReportNote | None = None


class WorkRightsReport(WorkRights):
    quote_verified: bool


class StatusCounts(BaseModel):
    met: int
    partial: int
    missing: int


class ScoreBreakdown(BaseModel):
    overall: int = Field(description="0-100, computed in code from the requirement statuses")
    must_have: float | None = Field(description="Share of must-have credit earned, 0-1, or null if none")
    nice_to_have: float | None = Field(description="Share of nice-to-have credit earned, 0-1, or null if none")
    counts: StatusCounts


class GroundingStats(BaseModel):
    """How much of the model's answer failed verification and was removed."""

    evidence_cited: int
    evidence_removed: int
    suggestions_proposed: int
    suggestions_removed: int
    requirements_downgraded: int


class AnalysisResult(BaseModel):
    job_title: str
    company: str
    provider: str
    language: Language
    work_rights: WorkRightsReport
    score: ScoreBreakdown
    requirements: list[RequirementReport]
    missing_keywords: list[str]
    suggestions: list[Suggestion]
    summary: str
    grounding: GroundingStats
