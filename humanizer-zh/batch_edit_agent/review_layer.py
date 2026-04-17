from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from .contracts import (
    ConfidenceBand,
    MatchItem,
    MatchStatus,
    OverviewStats,
    Stage1Decision,
)


Stage1Handler = Callable[[OverviewStats], Stage1Decision]
Stage2Handler = Callable[[MatchItem], tuple[str, str]]


def default_stage1_handler(overview: OverviewStats) -> Stage1Decision:
    print("\n=== Stage 1: Overview Confirmation ===")
    print(f"total_found: {overview.total_found}")
    print(f"file_count: {overview.file_count}")
    print(f"by_type: {overview.by_type}")
    print(f"by_band: {overview.by_band}")
    print("action options: [approve_all | exact_only | revise]")
    action = input("choose action: ").strip() or "revise"
    return Stage1Decision(action=action, comment="manual")


def apply_stage1_decision(matches: list[MatchItem], decision: Stage1Decision) -> list[MatchItem]:
    if decision.action == "approve_all":
        for item in matches:
            if item.confidence_band == ConfidenceBand.LOW and item.match_type.value == "similar":
                item.status = MatchStatus.SKIPPED
                item.reason = "low confidence similar match"
            else:
                item.status = MatchStatus.PENDING
        return matches

    if decision.action == "exact_only":
        for item in matches:
            if item.match_type.value == "exact":
                item.status = MatchStatus.PENDING
            else:
                item.status = MatchStatus.SKIPPED
                item.reason = "stage1 exact_only"
        return matches

    for item in matches:
        item.status = MatchStatus.SKIPPED
        item.reason = "stage1 revise requested"
    return matches


def default_stage2_handler(item: MatchItem) -> tuple[str, str]:
    print("\n--- Stage 2: Item Review ---")
    print(f"id: {item.id}")
    print(f"file: {item.file_path}:{item.line_start}-{item.line_end}")
    print(f"type: {item.match_type.value}, confidence: {item.confidence}")
    print(f"before: {item.before_snippet}")
    print(f"after : {item.after_preview}")
    print("decision options: [approve | skip | edit]")
    action = input("choose action: ").strip() or "skip"
    if action == "edit":
        replacement = input("manual replacement preview: ").rstrip("\n")
        return action, replacement
    return action, ""


def run_stage2_review(
    matches: list[MatchItem],
    reviewer: str,
    stage2_handler: Stage2Handler | None = None,
) -> tuple[list[MatchItem], dict[str, str]]:
    handler = stage2_handler or default_stage2_handler
    approved_at = datetime.now(timezone.utc).isoformat()
    confirmations: dict[str, str] = {}

    for item in matches:
        if item.status != MatchStatus.PENDING:
            continue
        action, payload = handler(item)
        if action == "approve":
            item.status = MatchStatus.APPROVED
            item.reason = f"approved by {reviewer} at {approved_at}"
            confirmations[item.id] = approved_at
            continue
        if action == "edit":
            item.status = MatchStatus.APPROVED
            item.after_preview = payload
            item.replacement_fragment = payload
            item.reason = f"manually edited+approved by {reviewer} at {approved_at}"
            confirmations[item.id] = approved_at
            continue
        item.status = MatchStatus.SKIPPED
        item.reason = f"skipped by {reviewer} at {approved_at}"

    return matches, confirmations

