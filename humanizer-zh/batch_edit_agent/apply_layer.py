from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .contracts import EditLogEntry, MatchItem, MatchStatus


def apply_approved_matches(
    root_dir: Path,
    matches: list[MatchItem],
    reviewer: str,
    confirmations: dict[str, str],
) -> tuple[list[MatchItem], list[EditLogEntry], list[str]]:
    grouped: dict[str, list[MatchItem]] = defaultdict(list)
    for item in matches:
        if item.status == MatchStatus.APPROVED:
            grouped[item.file_path].append(item)

    logs: list[EditLogEntry] = []
    failures: list[str] = []

    for rel_path, items in grouped.items():
        file_path = (root_dir / rel_path).resolve()
        try:
            original = file_path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{rel_path}: failed to read ({exc})")
            for item in items:
                item.status = MatchStatus.FAILED
            continue

        mutated = original
        before_snapshot = original
        file_failed = False
        file_errors: list[str] = []

        for item in items:
            before_fragment = item.source_fragment or ""
            after_fragment = item.replacement_fragment or item.after_preview

            if item.match_type.value == "exact":
                if before_fragment not in mutated:
                    item.status = MatchStatus.FAILED
                    file_failed = True
                    file_errors.append(f"{item.id}: source fragment not found")
                    continue
                mutated = mutated.replace(before_fragment, after_fragment, 1)
            else:
                lines = mutated.splitlines()
                index = item.line_start - 1
                if index < 0 or index >= len(lines):
                    item.status = MatchStatus.FAILED
                    file_failed = True
                    file_errors.append(f"{item.id}: line out of range")
                    continue
                lines[index] = after_fragment
                mutated = "\n".join(lines)
                if mutated and original.endswith("\n"):
                    mutated += "\n"

            item.status = MatchStatus.APPLIED
            logs.append(
                EditLogEntry(
                    match_id=item.id,
                    file_path=rel_path,
                    line_start=item.line_start,
                    line_end=item.line_end,
                    before=item.before_snippet,
                    after=item.after_preview,
                    confirmed_by=reviewer,
                    confirmed_at=confirmations.get(item.id, ""),
                    apply_at=datetime.now(timezone.utc).isoformat(),
                    result="applied",
                )
            )

        if file_failed:
            # rollback this file as atomic unit
            mutated = before_snapshot
            for item in items:
                if item.status == MatchStatus.APPLIED:
                    item.status = MatchStatus.FAILED
            failures.append(f"{rel_path}: rollback ({'; '.join(file_errors)})")
            continue

        if mutated != original:
            try:
                file_path.write_text(mutated, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{rel_path}: write failed ({exc})")
                for item in items:
                    item.status = MatchStatus.FAILED
                continue

    return matches, logs, failures

