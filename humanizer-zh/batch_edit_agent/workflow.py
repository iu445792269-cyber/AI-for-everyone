from __future__ import annotations

import json
from pathlib import Path

from .apply_layer import apply_approved_matches
from .contracts import ChangeRequest, MatchStatus, RunReport
from .review_layer import (
    Stage1Handler,
    Stage2Handler,
    apply_stage1_decision,
    default_stage1_handler,
    run_stage2_review,
)
from .search_layer import count_residual_matches, search_matches


def run_workflow(
    request: ChangeRequest,
    reviewer: str,
    stage1_handler: Stage1Handler | None = None,
    stage2_handler: Stage2Handler | None = None,
) -> tuple[RunReport, list]:
    matches, overview = search_matches(request)

    stage1 = (stage1_handler or default_stage1_handler)(overview)
    matches = apply_stage1_decision(matches, stage1)
    if stage1.action == "revise":
        report = RunReport(
            request=request,
            total_found=len(matches),
            total_approved=0,
            total_applied=0,
            total_skipped=len(matches),
            total_failed=0,
            residual_matches=count_residual_matches(request),
            overview=overview,
            entries=[],
            failures=["stage1 requested revise; no write executed"],
        )
        return report, matches

    matches, confirmations = run_stage2_review(matches, reviewer, stage2_handler=stage2_handler)
    matches, logs, failures = apply_approved_matches(
        root_dir=request.root_dir,
        matches=matches,
        reviewer=reviewer,
        confirmations=confirmations,
    )

    report = RunReport(
        request=request,
        total_found=len(matches),
        total_approved=sum(1 for m in matches if m.status in {MatchStatus.APPROVED, MatchStatus.APPLIED}),
        total_applied=sum(1 for m in matches if m.status == MatchStatus.APPLIED),
        total_skipped=sum(1 for m in matches if m.status == MatchStatus.SKIPPED),
        total_failed=sum(1 for m in matches if m.status == MatchStatus.FAILED),
        residual_matches=count_residual_matches(request),
        overview=overview,
        entries=logs,
        failures=failures,
    )
    return report, matches


def write_report(report: RunReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

