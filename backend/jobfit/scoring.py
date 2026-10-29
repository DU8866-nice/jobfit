"""The match score is computed in code, not asked of the model.

A number a model makes up is hard to explain and changes from run to run. Here the
model only labels each requirement met / partial / missing (and those labels are
checked against the resume), and the score follows from a fixed formula:

    credit:  met = 1, partial = 0.5, missing = 0
    overall = 75% x (must-have credit share) + 25% x (nice-to-have credit share)

If the ad has only one kind of requirement, that kind counts for 100%.
"""

from __future__ import annotations

from collections.abc import Iterable

from .schemas import Importance, MatchStatus, ScoreBreakdown, StatusCounts

CREDIT: dict[str, float] = {"met": 1.0, "partial": 0.5, "missing": 0.0}
MUST_HAVE_WEIGHT = 0.75


def _share(statuses: list[str]) -> float | None:
    if not statuses:
        return None
    return sum(CREDIT[s] for s in statuses) / len(statuses)


def compute_score(items: Iterable[tuple[Importance, MatchStatus]]) -> ScoreBreakdown:
    items = list(items)
    must = [status for importance, status in items if importance == "must_have"]
    nice = [status for importance, status in items if importance == "nice_to_have"]

    must_share = _share(must)
    nice_share = _share(nice)

    if must_share is not None and nice_share is not None:
        combined = MUST_HAVE_WEIGHT * must_share + (1 - MUST_HAVE_WEIGHT) * nice_share
    elif must_share is not None:
        combined = must_share
    elif nice_share is not None:
        combined = nice_share
    else:
        combined = 0.0

    statuses = [status for _, status in items]
    return ScoreBreakdown(
        overall=round(combined * 100),
        must_have=None if must_share is None else round(must_share, 3),
        nice_to_have=None if nice_share is None else round(nice_share, 3),
        counts=StatusCounts(
            met=statuses.count("met"),
            partial=statuses.count("partial"),
            missing=statuses.count("missing"),
        ),
    )
