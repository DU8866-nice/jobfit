"""The analysis pipeline.

1. Extract requirements from the job ad (model call 1).
2. Match the resume against them (model call 2).
3. Verify: keep only evidence and suggestions that can be found in the resume,
   downgrade requirements whose evidence did not survive, and drop rewrites that
   introduce skills the resume doesn't show.
4. Score and list missing keywords in code, so the numbers are reproducible.
"""

from __future__ import annotations

from .errors import AppError
from .grounding import Grounder
from .llm.base import LLMClient
from .schemas import (
    AnalysisResult,
    ExtractionResult,
    GroundingStats,
    Language,
    MatchResult,
    Requirement,
    RequirementReport,
    Suggestion,
    WorkRightsReport,
)
from .scoring import compute_score

MIN_INPUT_CHARS = 50
MAX_REQUIREMENTS = 25
MAX_EVIDENCE_PER_REQUIREMENT = 2
MAX_SUGGESTIONS = 5

# The model skipped this requirement, so it is counted as missing.
NOTE_NOT_ASSESSED = "not_assessed"
# The model said met/partial, but none of its quotes are in the resume, so it is counted as missing.
NOTE_DOWNGRADED = "evidence_not_found"


class InputError(AppError):
    """The user's input can't be analysed."""


class AnalysisError(AppError):
    """The analysis produced nothing usable."""


def analyze(
    job_description: str,
    resume_text: str,
    client: LLMClient,
    *,
    language: Language = "en",
    max_chars: int = 30_000,
) -> AnalysisResult:
    job_description = job_description.strip()
    resume_text = resume_text.strip()
    _check_length("job", "job description", job_description, max_chars)
    _check_length("resume", "resume", resume_text, max_chars)

    extraction = client.extract_requirements(job_description, language)
    requirements = normalize_requirements(extraction.requirements)
    if not requirements:
        raise AnalysisError("no_requirements", "No requirements could be found in this job description.")

    match = client.match_resume(requirements, resume_text, language)
    return build_result(
        extraction=extraction,
        requirements=requirements,
        match=match,
        job_description=job_description,
        resume_text=resume_text,
        provider=client.name,
        language=language,
    )


def _check_length(field: str, label: str, text: str, max_chars: int) -> None:
    if len(text) < MIN_INPUT_CHARS:
        raise InputError(f"{field}_too_short", f"The {label} is too short to analyse.")
    if len(text) > max_chars:
        raise InputError(f"{field}_too_long", f"The {label} is longer than {max_chars:,} characters. Please shorten it.")


def normalize_requirements(requirements: list[Requirement]) -> list[Requirement]:
    """Drop empty items, de-duplicate keywords, and renumber ids R1..Rn so they are unique."""
    cleaned: list[Requirement] = []
    for req in requirements:
        text = req.text.strip()
        if not text:
            continue
        keywords: list[str] = []
        for keyword in req.keywords:
            keyword = keyword.strip()
            if keyword and keyword.lower() not in {k.lower() for k in keywords}:
                keywords.append(keyword)
        cleaned.append(req.model_copy(update={"id": f"R{len(cleaned) + 1}", "text": text, "keywords": keywords}))
        if len(cleaned) == MAX_REQUIREMENTS:
            break
    return cleaned


def build_result(
    *,
    extraction: ExtractionResult,
    requirements: list[Requirement],
    match: MatchResult,
    job_description: str,
    resume_text: str,
    provider: str,
    language: Language = "en",
) -> AnalysisResult:
    resume = Grounder(resume_text)
    ad = Grounder(job_description)

    matches = {}
    for m in match.matches:
        matches.setdefault(m.requirement_id, m)  # if the model repeats an id, the first answer wins

    reports: list[RequirementReport] = []
    evidence_cited = evidence_removed = downgraded = 0

    for req in requirements:
        m = matches.get(req.id)
        if m is None:
            reports.append(
                RequirementReport(**req.model_dump(), status="missing", evidence=[], explanation="", note=NOTE_NOT_ASSESSED)
            )
            continue

        status, note = m.status, None
        quotes = [q.strip() for q in m.evidence if q.strip()] if status != "missing" else []
        evidence_cited += len(quotes)
        kept: list[str] = []
        for quote in quotes:
            if resume.contains(quote) and quote not in kept:
                kept.append(quote)
        evidence_removed += len(quotes) - len(kept)
        kept = kept[:MAX_EVIDENCE_PER_REQUIREMENT]

        if status != "missing" and not kept:
            status, note = "missing", NOTE_DOWNGRADED
            downgraded += 1

        reports.append(
            RequirementReport(
                **req.model_dump(), status=status, evidence=kept, explanation=m.explanation.strip(), note=note
            )
        )

    suggestions, suggestions_removed = _verified_suggestions(match.suggestions, requirements, resume)

    work_rights = extraction.work_rights
    quote = work_rights.quote.strip()
    work_rights_report = WorkRightsReport(
        status=work_rights.status,
        detail=work_rights.detail.strip(),
        quote=quote,
        quote_verified=bool(quote) and ad.contains(quote),
    )

    return AnalysisResult(
        job_title=extraction.job_title.strip() or "Untitled role",
        company=extraction.company.strip(),
        provider=provider,
        language=language,
        work_rights=work_rights_report,
        score=compute_score((r.importance, r.status) for r in reports),
        requirements=reports,
        missing_keywords=_missing_keywords(reports, resume),
        suggestions=suggestions,
        summary=match.summary.strip(),
        grounding=GroundingStats(
            evidence_cited=evidence_cited,
            evidence_removed=evidence_removed,
            suggestions_proposed=len(match.suggestions),
            suggestions_removed=suggestions_removed,
            requirements_downgraded=downgraded,
        ),
    )


def _verified_suggestions(
    proposed: list[Suggestion], requirements: list[Requirement], resume: Grounder
) -> tuple[list[Suggestion], int]:
    """Keep a suggestion only if its original line is in the resume and its rewrite adds no new skills."""
    known_ids = {r.id for r in requirements}
    all_keywords = {k for r in requirements for k in r.keywords}

    kept: list[Suggestion] = []
    removed = 0
    for s in proposed:
        original, rewrite = s.original.strip(), s.rewrite.strip()
        if not original or not rewrite or not resume.contains(original):
            removed += 1
            continue
        rewrite_text = Grounder(rewrite)
        introduces_new_skill = any(rewrite_text.contains(k) and not resume.contains(k) for k in all_keywords)
        if introduces_new_skill:
            removed += 1
            continue
        if len(kept) < MAX_SUGGESTIONS:
            kept.append(
                Suggestion(
                    requirement_ids=[i for i in s.requirement_ids if i in known_ids],
                    original=original,
                    rewrite=rewrite,
                    rationale=s.rationale.strip(),
                )
            )
    return kept, removed


def _missing_keywords(reports: list[RequirementReport], resume: Grounder) -> list[str]:
    """Job-ad terms from unmet requirements that don't appear anywhere in the resume. Must-haves first."""
    ordered = sorted(reports, key=lambda r: r.importance != "must_have")
    seen: set[str] = set()
    result: list[str] = []
    for report in ordered:
        if report.status == "met":
            continue
        for keyword in report.keywords:
            key = keyword.lower()
            if key not in seen and not resume.contains(keyword):
                seen.add(key)
                result.append(keyword)
    return result
