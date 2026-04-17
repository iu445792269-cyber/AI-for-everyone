from __future__ import annotations

import json
from pathlib import Path

from batch_edit_agent.contracts import ChangeRequest, ScopeFilter, Stage1Decision
from batch_edit_agent.workflow import run_workflow, write_report


def _make_request(root: Path) -> ChangeRequest:
    return ChangeRequest(
        source_text="A",
        target_text="B",
        root_dir=root,
        scope=ScopeFilter(
            include_globs=["docs/**/*.md"],
            exclude_globs=[],
            file_extensions=[".md"],
        ),
    )


def test_exact_match_apply_and_report(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    file_path = docs / "pilot.md"
    file_path.write_text("line1\nA\nline3\n", encoding="utf-8")

    req = _make_request(tmp_path)

    def stage1(_overview):
        return Stage1Decision(action="approve_all")

    def stage2(_item):
        return "approve", ""

    report, matches = run_workflow(req, reviewer="tester", stage1_handler=stage1, stage2_handler=stage2)
    updated = file_path.read_text(encoding="utf-8")

    assert "B" in updated
    assert report.total_found >= 1
    assert report.total_applied >= 1
    assert all(m.status.value in {"applied", "skipped"} for m in matches)

    out = tmp_path / "reports" / "r.json"
    write_report(report, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "totals" in data
    assert "entries" in data


def test_stage1_revise_stops_write(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    file_path = docs / "pilot.md"
    before = "A\nA\n"
    file_path.write_text(before, encoding="utf-8")

    req = _make_request(tmp_path)

    def stage1(_overview):
        return Stage1Decision(action="revise")

    report, _ = run_workflow(req, reviewer="tester", stage1_handler=stage1)

    assert file_path.read_text(encoding="utf-8") == before
    assert report.total_applied == 0
    assert report.total_skipped >= 0

