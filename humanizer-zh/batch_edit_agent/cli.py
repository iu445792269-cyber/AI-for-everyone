from __future__ import annotations

import argparse
from pathlib import Path

from .contracts import ChangeRequest, ScopeFilter
from .workflow import run_workflow, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safe batch replacement workflow")
    parser.add_argument("--source", required=True, help="source text to search")
    parser.add_argument("--target", required=True, help="target text to replace")
    parser.add_argument("--root", default=".", help="root directory")
    parser.add_argument("--include", default="**/*", help="comma separated include globs")
    parser.add_argument("--exclude", default="", help="comma separated extra exclude globs")
    parser.add_argument("--ext", default="", help="comma separated extension filters, e.g. .md,.txt")
    parser.add_argument("--reviewer", default="manual-reviewer", help="reviewer id")
    parser.add_argument("--report", default="reports/batch-edit-report.json", help="report output path")
    parser.add_argument("--similar-threshold", type=float, default=0.78)
    parser.add_argument("--medium-threshold", type=float, default=0.62)
    parser.add_argument("--low-threshold", type=float, default=0.45)
    return parser.parse_args()


def _split_csv(raw: str) -> list[str]:
    values = [part.strip() for part in raw.split(",")]
    return [item for item in values if item]


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    default_excludes = ScopeFilter().exclude_globs
    scope = ScopeFilter(
        include_globs=_split_csv(args.include) or ["**/*"],
        exclude_globs=default_excludes + _split_csv(args.exclude),
        file_extensions=_split_csv(args.ext),
    )
    req = ChangeRequest(
        source_text=args.source,
        target_text=args.target,
        root_dir=root,
        scope=scope,
        similar_threshold=args.similar_threshold,
        medium_threshold=args.medium_threshold,
        low_threshold=args.low_threshold,
        created_by=args.reviewer,
    )

    report, _ = run_workflow(req, reviewer=args.reviewer)
    output = (root / args.report).resolve()
    write_report(report, output)

    print(f"report written to: {output}")
    print(f"found={report.total_found}, applied={report.total_applied}, failed={report.total_failed}")


if __name__ == "__main__":
    main()

