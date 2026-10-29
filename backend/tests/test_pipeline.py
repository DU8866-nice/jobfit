"""The verification layer: what happens when the model gets things wrong."""

import pytest

from jobfit.pipeline import AnalysisError, InputError, analyze
from jobfit.schemas import (
    ExtractionResult,
    MatchResult,
    Requirement,
    RequirementMatch,
    Suggestion,
    WorkRights,
)


def req(id_, text, importance="must_have", keywords=()):
    return Requirement(id=id_, text=text, importance=importance, category="skill", keywords=list(keywords))


class FakeClient:
    """Returns canned model output and records what it was asked."""

    name = "fake"

    def __init__(self, extraction, match):
        self._extraction = extraction
        self._match = match
        self.seen_requirement_ids = None
        self.languages = []

    def extract_requirements(self, job_description, language):
        self.languages.append(language)
        return self._extraction

    def match_resume(self, requirements, resume_text, language):
        self.languages.append(language)
        self.seen_requirement_ids = [r.id for r in requirements]
        return self._match


@pytest.fixture
def extraction():
    return ExtractionResult(
        job_title="  Junior Data Analyst ",
        company="Bright Harbour Analytics",
        requirements=[
            req("R1", "SQL for querying data", keywords=["SQL", "sql"]),
            req("R1", "Dashboards in Power BI", keywords=["Power BI"]),  # duplicate id from the model
            req("R9", "   "),  # empty, should be dropped
            req("R4", "Python for data cleaning", keywords=["Python", "pandas"]),
            req("R5", "Stakeholder communication"),
            req("R6", "Cloud exposure", importance="nice_to_have", keywords=["AWS"]),
        ],
        work_rights=WorkRights(
            status="required",
            detail="Full working rights required",
            quote="Applicants must have full working rights in Australia.",
        ),
    )


def test_requirements_are_renumbered_before_matching(job_ad, resume, extraction):
    client = FakeClient(extraction, MatchResult(matches=[], suggestions=[], summary=""))
    result = analyze(job_ad, resume, client)
    assert client.seen_requirement_ids == ["R1", "R2", "R3", "R4", "R5"]
    assert [r.text for r in result.requirements][:2] == ["SQL for querying data", "Dashboards in Power BI"]
    assert result.requirements[0].keywords == ["SQL"], "case-insensitive duplicate keyword removed"


def test_language_is_passed_to_both_steps_and_returned(job_ad, resume, extraction):
    client = FakeClient(extraction, MatchResult(matches=[], suggestions=[], summary=""))
    result = analyze(job_ad, resume, client, language="zh")
    assert client.languages == ["zh", "zh"]
    assert result.language == "zh"


def test_made_up_evidence_is_removed_and_status_downgraded(job_ad, resume, extraction):
    match = MatchResult(
        matches=[
            # Real quote: kept.
            RequirementMatch(requirement_id="R1", status="met", evidence=["Wrote SQL queries to join sales and inventory tables"], explanation="ok"),
            # Invented quote: removed, and with no evidence left the requirement becomes missing.
            RequirementMatch(requirement_id="R2", status="met", evidence=["Built Power BI dashboards for executives"], explanation="claims Power BI"),
            # One real and one invented quote: the real one is kept, status stays partial.
            RequirementMatch(requirement_id="R3", status="partial", evidence=["Customer churn analysis with pandas and scikit-learn", "Led a Python guild"], explanation="some"),
            # R4 is not assessed at all.
            # Duplicate answer for R1: ignored.
            RequirementMatch(requirement_id="R1", status="missing", evidence=[], explanation="dupe"),
            # Unknown id: ignored.
            RequirementMatch(requirement_id="R99", status="met", evidence=[], explanation="?"),
            RequirementMatch(requirement_id="R5", status="missing", evidence=["should be ignored"], explanation="no cloud"),
        ],
        suggestions=[],
        summary=" Solid SQL; no Power BI. ",
    )
    result = analyze(job_ad, resume, FakeClient(extraction, match))
    by_id = {r.id: r for r in result.requirements}

    assert by_id["R1"].status == "met"
    assert by_id["R1"].evidence == ["Wrote SQL queries to join sales and inventory tables"]

    assert by_id["R2"].status == "missing"
    assert by_id["R2"].evidence == []
    assert by_id["R2"].note == "evidence_not_found"

    assert by_id["R3"].status == "partial"
    assert by_id["R3"].evidence == ["Customer churn analysis with pandas and scikit-learn"]

    assert by_id["R4"].status == "missing"
    assert by_id["R4"].note == "not_assessed"

    assert by_id["R5"].evidence == [], "missing requirements never show evidence"

    assert result.grounding.evidence_cited == 4
    assert result.grounding.evidence_removed == 2
    assert result.grounding.requirements_downgraded == 1
    assert result.summary == "Solid SQL; no Power BI."
    assert result.job_title == "Junior Data Analyst"


def test_score_and_missing_keywords_are_computed_from_verified_statuses(job_ad, resume, extraction):
    match = MatchResult(
        matches=[
            RequirementMatch(requirement_id="R1", status="met", evidence=["SQL"], explanation=""),
            RequirementMatch(requirement_id="R2", status="met", evidence=["Power BI expert"], explanation=""),
            RequirementMatch(requirement_id="R3", status="met", evidence=["Python"], explanation=""),
            RequirementMatch(requirement_id="R4", status="partial", evidence=["Presented findings to store managers every fortnight"], explanation=""),
            RequirementMatch(requirement_id="R5", status="missing", evidence=[], explanation=""),
        ],
        suggestions=[],
        summary="",
    )
    result = analyze(job_ad, resume, FakeClient(extraction, match))
    # must-haves: met, missing (downgraded), met, partial -> 2.5 / 4 ; nice: 0 -> 0.75 * 0.625 = 0.469
    assert result.score.overall == 47
    assert result.score.counts.model_dump() == {"met": 2, "partial": 1, "missing": 2}
    assert result.missing_keywords == ["Power BI", "AWS"]


def test_suggestions_must_quote_the_resume_and_add_no_new_skills(job_ad, resume, extraction):
    match = MatchResult(
        matches=[],
        suggestions=[
            Suggestion(
                requirement_ids=["R1", "R42"],
                original="Wrote SQL queries to join sales and inventory tables for weekly reporting",
                rewrite="Wrote SQL queries joining sales and inventory tables to automate weekly reporting for [number] stores",
                rationale="Mirrors the ad's wording.",
            ),
            Suggestion(
                requirement_ids=["R2"],
                original="Built Power BI dashboards",  # not in the resume
                rewrite="Built Power BI dashboards used daily",
                rationale="",
            ),
            Suggestion(
                requirement_ids=["R2"],
                original="Built Tableau dashboards for the store operations team",
                rewrite="Built Tableau and Power BI dashboards for the store operations team",  # invents Power BI
                rationale="",
            ),
            Suggestion(requirement_ids=["R1"], original="SQL", rewrite="   ", rationale=""),  # empty rewrite
        ],
        summary="",
    )
    result = analyze(job_ad, resume, FakeClient(extraction, match))
    assert len(result.suggestions) == 1
    kept = result.suggestions[0]
    assert kept.requirement_ids == ["R1"], "unknown requirement ids are dropped"
    assert result.grounding.suggestions_proposed == 4
    assert result.grounding.suggestions_removed == 3


def test_work_rights_quote_is_verified_against_the_ad(job_ad, resume, extraction):
    result = analyze(job_ad, resume, FakeClient(extraction, MatchResult(matches=[], suggestions=[], summary="")))
    assert result.work_rights.status == "required"
    assert result.work_rights.quote_verified is True

    invented = extraction.model_copy(
        update={"work_rights": WorkRights(status="required", detail="", quote="Must be an Australian citizen.")}
    )
    result = analyze(job_ad, resume, FakeClient(invented, MatchResult(matches=[], suggestions=[], summary="")))
    assert result.work_rights.quote_verified is False


@pytest.mark.parametrize(
    "jd, cv, code",
    [
        ("too short", "x" * 100, "job_too_short"),
        ("x" * 100, "short", "resume_too_short"),
        ("x" * 40_000, "x" * 100, "job_too_long"),
    ],
)
def test_input_length_is_checked_before_calling_the_model(extraction, jd, cv, code):
    client = FakeClient(extraction, None)
    with pytest.raises(InputError) as info:
        analyze(jd, cv, client)
    assert info.value.code == code
    assert client.languages == [], "no model call for invalid input"


def test_no_requirements_is_an_error(job_ad, resume):
    empty = ExtractionResult(
        job_title="x", company="", requirements=[], work_rights=WorkRights(status="not_mentioned", detail="", quote="")
    )
    with pytest.raises(AnalysisError) as info:
        analyze(job_ad, resume, FakeClient(empty, None))
    assert info.value.code == "no_requirements"
