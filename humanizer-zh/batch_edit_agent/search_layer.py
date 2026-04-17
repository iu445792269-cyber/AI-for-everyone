from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from .contracts import (
    ChangeRequest,
    ConfidenceBand,
    MatchItem,
    MatchType,
    OverviewStats,
)


@dataclass(slots=True)
class FileScanResult:
    path: Path
    text: str


def _normalize_for_similarity(value: str) -> str:
    value = value.lower()
    value = value.replace("，", ",").replace("。", ".").replace("：", ":").replace("；", ";")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _confidence_band(score: float, req: ChangeRequest) -> ConfidenceBand:
    if score >= req.similar_threshold:
        return ConfidenceBand.HIGH
    if score >= req.medium_threshold:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW


def iter_candidate_files(req: ChangeRequest) -> list[Path]:
    root = req.root_dir.resolve()
    include: set[Path] = set()
    for pattern in req.scope.include_globs:
        include.update(root.glob(pattern))

    excluded: set[Path] = set()
    for pattern in req.scope.exclude_globs:
        excluded.update(root.glob(pattern))

    files: list[Path] = []
    for path in include:
        if path in excluded or path.is_dir():
            continue
        if req.scope.file_extensions and path.suffix not in req.scope.file_extensions:
            continue
        files.append(path)
    return sorted(files)


def _safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError:
        return None


def search_matches(req: ChangeRequest) -> tuple[list[MatchItem], OverviewStats]:
    source_norm = _normalize_for_similarity(req.source_text)
    all_matches: list[MatchItem] = []
    dedupe: set[tuple[str, int, int]] = set()
    per_dir = defaultdict(int)
    per_type = defaultdict(int)
    per_band = defaultdict(int)
    idx = 0

    for path in iter_candidate_files(req):
        text = _safe_read_text(path)
        if text is None:
            continue
        lines = text.splitlines()
        rel = str(path.relative_to(req.root_dir))

        # Exact match phase
        for line_no, line in enumerate(lines, start=1):
            cursor = 0
            while True:
                pos = line.find(req.source_text, cursor)
                if pos == -1:
                    break
                key = (rel, line_no, line_no)
                if key not in dedupe:
                    idx += 1
                    before = line
                    after = line[:pos] + req.target_text + line[pos + len(req.source_text) :]
                    match = MatchItem(
                        id=f"M{idx:06d}",
                        file_path=rel,
                        line_start=line_no,
                        line_end=line_no,
                        match_type=MatchType.EXACT,
                        confidence=1.0,
                        confidence_band=ConfidenceBand.HIGH,
                        before_snippet=before,
                        after_preview=after,
                        source_fragment=req.source_text,
                        replacement_fragment=req.target_text,
                    )
                    all_matches.append(match)
                    dedupe.add(key)
                    per_dir[str(Path(rel).parent)] += 1
                    per_type[match.match_type.value] += 1
                    per_band[match.confidence_band.value] += 1
                cursor = pos + max(len(req.source_text), 1)

        # Similar match phase (line-level)
        for line_no, line in enumerate(lines, start=1):
            line_norm = _normalize_for_similarity(line)
            if not line_norm:
                continue
            score = SequenceMatcher(None, source_norm, line_norm).ratio()
            if score < req.low_threshold:
                continue
            key = (rel, line_no, line_no)
            if key in dedupe:
                continue
            band = _confidence_band(score, req)
            idx += 1
            after_preview = req.target_text if band != ConfidenceBand.LOW else line
            match = MatchItem(
                id=f"M{idx:06d}",
                file_path=rel,
                line_start=line_no,
                line_end=line_no,
                match_type=MatchType.SIMILAR,
                confidence=round(score, 4),
                confidence_band=band,
                before_snippet=line,
                after_preview=after_preview,
                source_fragment=line,
                replacement_fragment=req.target_text if band != ConfidenceBand.LOW else line,
            )
            all_matches.append(match)
            dedupe.add(key)
            per_dir[str(Path(rel).parent)] += 1
            per_type[match.match_type.value] += 1
            per_band[match.confidence_band.value] += 1

    overview = OverviewStats(
        total_found=len(all_matches),
        file_count=len({m.file_path for m in all_matches}),
        by_dir=dict(sorted(per_dir.items(), key=lambda x: x[0])),
        by_type=dict(sorted(per_type.items(), key=lambda x: x[0])),
        by_band=dict(sorted(per_band.items(), key=lambda x: x[0])),
    )
    return all_matches, overview


def count_residual_matches(req: ChangeRequest) -> int:
    total = 0
    for path in iter_candidate_files(req):
        text = _safe_read_text(path)
        if text is None:
            continue
        total += text.count(req.source_text)
    return total

