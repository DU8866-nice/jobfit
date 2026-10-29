"""Run the evaluation set and report how well a provider does.

Each case in evals/cases/ is an invented job ad and resume, plus what a careful
human reviewer would expect:

* requirement statuses ("SQL" should be met, "Power BI" missing, ...)
* whether the ad states a work-rights condition

The report covers:

* status accuracy: expected statuses the provider got exactly right
* work-rights accuracy
* grounding: share of the quotes the model cited that were really in the resume
  (anything below 100% means the model invented evidence, which the app removed)
* time and tokens per analysis, for cost estimates

Usage, from the backend folder:

    python -m evals.run_evals                         # provider chosen from env (mock if no key)
    JOBFIT_PROVIDER=deepseek python -m evals.run_evals
    python -m evals.run_evals --save --markdown report.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from jobfit.config import Settings
from jobfit.errors import AppError
from jobfit.llm import get_client
from jobfit.llm.base import UsageTotals
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


def _usage(client) -> UsageTotals:
    meter = getattr(client, "usage", None)
    return meter.snapshot() if meter is not None else UsageTotals()


def run_case(path: Path, client) -> dict:
    case = json.loads(path.read_text(encoding="utf-8"))
    report: dict = {"case": path.stem, "note": case.get("note", "")}
    before = _usage(client)
    started = time.monotonic()
    try:
        result = analyze(case["job_description"], case["resume"], client, language=case.get("language", "en"))
    except AppError as exc:
        report.update(error=f"{exc.code}: {exc.message}", seconds=round(time.monotonic() - started, 1), checks=[])
        return report
    used = _usage(client) - before

    checks = []
    for expected in case["expected"]["requirements"]:
        req = find_requirement(result, expected["match"])
        checks.append(
            {
                "match": expected["match"],
                "expected": expected["status"],
                "actual": req.status if req else "not found",
                "ok": bool(req) and req.status == expected["status"],
                "requirement": req.text if req else None,
                "explanation": req.explanation if req else None,
                "note": req.note if req else None,
            }
        )

    expected_rights = case["expected"]["work_rights_mentioned"]
    report.update(
        seconds=round(time.monotonic() - started, 1),
        checks=checks,
        work_rights_ok=expected_rights == (result.work_rights.status != "not_mentioned"),
        work_rights=result.work_rights.status,
        requirements_found=len(result.requirements),
        evidence_cited=result.grounding.evidence_cited,
        evidence_removed=result.grounding.evidence_removed,
        suggestions_proposed=result.grounding.suggestions_proposed,
        suggestions_removed=result.grounding.suggestions_removed,
        score=result.score.overall,
        calls=used.calls,
        input_tokens=used.input_tokens,
        output_tokens=used.output_tokens,
    )
    return report


def summarize(provider: str, models: dict, reports: list[dict]) -> dict:
    done = [r for r in reports if "error" not in r]
    checks = [c for r in done for c in r["checks"]]
    cited = sum(r["evidence_cited"] for r in done)
    removed = sum(r["evidence_removed"] for r in done)
    n = len(done) or 1
    return {
        "provider": provider,
        "models": models,
        "cases": len(reports),
        "errors": len(reports) - len(done),
        "status_correct": sum(c["ok"] for c in checks),
        "status_total": len(checks),
        "status_accuracy": round(sum(c["ok"] for c in checks) / len(checks), 3) if checks else None,
        "work_rights_correct": sum(r["work_rights_ok"] for r in done),
        "evidence_cited": cited,
        "evidence_removed": removed,
        "grounded_evidence_rate": round((cited - removed) / cited, 3) if cited else None,
        "suggestions_removed": sum(r["suggestions_removed"] for r in done),
        "avg_seconds": round(sum(r["seconds"] for r in done) / n, 1),
        "avg_input_tokens": round(sum(r["input_tokens"] for r in done) / n),
        "avg_output_tokens": round(sum(r["output_tokens"] for r in done) / n),
    }


def to_markdown(summary: dict, reports: list[dict]) -> str:
    models = ", ".join(f"{k} = `{v}`" for k, v in summary["models"].items()) or "n/a"
    commit = os.getenv("GITHUB_SHA", "")[:7]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pct = lambda v: "n/a" if v is None else f"{v:.1%}"  # noqa: E731

    lines = [
        f"## Evaluation: {summary['provider']}",
        "",
        f"Models: {models}. Run at {stamp}" + (f" on commit `{commit}`." if commit else "."),
        "",
        "| Metric | Result |",
        "| --- | --- |",
        f"| Requirement status accuracy | {pct(summary['status_accuracy'])} ({summary['status_correct']}/{summary['status_total']}) |",
        f"| Work-rights detection | {summary['work_rights_correct']}/{summary['cases'] - summary['errors']} |",
        f"| Quotes found in the resume | {pct(summary['grounded_evidence_rate'])} ({summary['evidence_cited'] - summary['evidence_removed']}/{summary['evidence_cited']}) |",
        f"| Suggested edits removed by checks | {summary['suggestions_removed']} |",
        f"| Average time per analysis | {summary['avg_seconds']}s |",
        f"| Average tokens per analysis | {summary['avg_input_tokens']:,} in, {summary['avg_output_tokens']:,} out |",
        f"| Cases that failed to run | {summary['errors']} |",
        "",
        "### Per case",
        "",
        "| Case | Statuses | Work rights | Score | Time | Tokens in / out |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in reports:
        if "error" in r:
            lines.append(f"| {r['case']} | error: {r['error']} | | | {r['seconds']}s | |")
            continue
        ok = sum(c["ok"] for c in r["checks"])
        lines.append(
            f"| {r['case']} | {ok}/{len(r['checks'])} | {'ok' if r['work_rights_ok'] else 'wrong'} ({r['work_rights']}) "
            f"| {r['score']} | {r['seconds']}s | {r['input_tokens']:,} / {r['output_tokens']:,} |"
        )

    misses = [(r["case"], c) for r in reports for c in r.get("checks", []) if not c["ok"]]
    if misses:
        lines += ["", "### Misses", ""]
        for case, c in misses:
            detail = f" Requirement: \"{c['requirement']}\". Explanation: \"{c['explanation']}\"" if c["requirement"] else ""
            note = f" (note: {c['note']})" if c["note"] else ""
            lines.append(f"- **{case}**, `{c['match']}`: expected {c['expected']}, got {c['actual']}{note}.{detail}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--save", action="store_true", help="write a JSON report to evals/results/")
    parser.add_argument("--markdown", type=Path, help="also write a Markdown report to this path")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    try:
        client = get_client(settings)
    except AppError as exc:
        message = f"Could not start provider {settings.provider!r}: {exc.message}"
        print(message, file=sys.stderr)
        if args.markdown:
            args.markdown.write_text(f"## Evaluation: {settings.provider}\n\n{message}\n", encoding="utf-8")
        return 1

    models = {
        k: v for k, v in (("extract", getattr(client, "extract_model", None)), ("match", getattr(client, "match_model", None))) if v
    }
    reports = [run_case(path, client) for path in sorted(CASES.glob("*.json"))]
    summary = summarize(client.name, models, reports)

    print(f"Provider: {client.name} {models}\n")
    for r in reports:
        if "error" in r:
            print(f"{r['case']}: ERROR {r['error']}")
            continue
        ok = sum(c["ok"] for c in r["checks"])
        print(f"{r['case']}  ({r['seconds']}s, score {r['score']}, tokens {r['input_tokens']}/{r['output_tokens']})")
        print(f"  statuses {ok}/{len(r['checks'])}   work rights {'ok' if r['work_rights_ok'] else 'WRONG'}")
        for c in r["checks"]:
            if not c["ok"]:
                print(f"    - {c['match']}: expected {c['expected']}, got {c['actual']}")
    print("\nSummary")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    if args.save:
        RESULTS.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = RESULTS / f"{stamp}-{client.name}.json"
        out.write_text(json.dumps({"summary": summary, "cases": reports}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved {out}")
    if args.markdown:
        args.markdown.write_text(to_markdown(summary, reports), encoding="utf-8")
        print(f"Wrote {args.markdown}")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
