"""Run the evaluation set and report how well a provider does.

Each case in evals/cases/ is an invented job ad and resume, plus what a careful
human reviewer would expect:

* requirement statuses ("SQL" should be met, "Power BI" missing, ...)
* whether the ad states a work-rights condition

The report covers three numbers:

* status accuracy: expected statuses the provider got exactly right
* work-rights accuracy
* grounding: share of the quotes the model cited that were really in the resume
  (anything below 100% means the model invented evidence, which the app removed)

Usage, from the backend folder:

    python -m evals.run_evals                      # provider chosen from env (mock if no key)
    JOBFIT_PROVIDER=anthropic python -m evals.run_evals
    python -m evals.run_evals --save               # also write a JSON report to evals/results/
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from jobfit.config import Settings
from jobfit.llm import get_client
from jobfit.pipeline import analyze
from jobfit.schemas import AnalysisResult

HERE = Path(__file__).parent
CASES = HERE / "cases"
RESULTS = HERE / "results"


def find_requirement(result: AnalysisResult, needle: str):
    """The first requirement whose text or keywords mention `needle` (case-insensitive)."""
    needle = needle.lower()
    for req in result.requirements:
        haystack = " ".join([req.text, *req.keywords]).lower()
        if needle in haystack:
            return req
    return None


def run_case(path: Path, client) -> dict:
    case = json.loads(path.read_text(encoding="utf-8"))
    started = time.monotonic()
    result = analyze(case["job_description"], case["resume"], client, language=case.get("language", "en"))
    seconds = round(time.monotonic() - started, 1)

    checks = []
    for expected in case["expected"]["requirements"]:
        req = find_requirement(result, expected["match"])
        checks.append(
            {
                "match": expected["match"],
                "expected": expected["status"],
                "actual": req.status if req else "not found",
                "ok": bool(req) and req.status == expected["status"],
            }
        )

    expected_rights = case["expected"]["work_rights_mentioned"]
    actual_rights = result.work_rights.status != "not_mentioned"
    return {
        "case": path.stem,
        "seconds": seconds,
        "checks": checks,
        "work_rights_ok": expected_rights == actual_rights,
        "evidence_cited": result.grounding.evidence_cited,
        "evidence_removed": result.grounding.evidence_removed,
        "suggestions_proposed": result.grounding.suggestions_proposed,
        "suggestions_removed": result.grounding.suggestions_removed,
        "score": result.score.overall,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--save", action="store_true", help="write a JSON report to evals/results/")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    client = get_client(settings)
    reports = [run_case(path, client) for path in sorted(CASES.glob("*.json"))]

    print(f"Provider: {client.name}\n")
    for report in reports:
        passed = sum(c["ok"] for c in report["checks"])
        print(f"{report['case']}  ({report['seconds']}s, score {report['score']})")
        print(f"  statuses {passed}/{len(report['checks'])}   work rights {'ok' if report['work_rights_ok'] else 'WRONG'}")
        for check in report["checks"]:
            if not check["ok"]:
                print(f"    - {check['match']}: expected {check['expected']}, got {check['actual']}")

    checks = [c for r in reports for c in r["checks"]]
    cited = sum(r["evidence_cited"] for r in reports)
    removed = sum(r["evidence_removed"] for r in reports)
    summary = {
        "provider": client.name,
        "cases": len(reports),
        "status_accuracy": round(sum(c["ok"] for c in checks) / len(checks), 3) if checks else None,
        "work_rights_accuracy": round(sum(r["work_rights_ok"] for r in reports) / len(reports), 3) if reports else None,
        "grounded_evidence_rate": round((cited - removed) / cited, 3) if cited else None,
        "suggestions_removed": sum(r["suggestions_removed"] for r in reports),
    }
    print("\nSummary")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    if args.save:
        RESULTS.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = RESULTS / f"{stamp}-{client.name}.json"
        out.write_text(json.dumps({"summary": summary, "cases": reports}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
