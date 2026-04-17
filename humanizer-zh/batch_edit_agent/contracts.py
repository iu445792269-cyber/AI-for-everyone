from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class MatchType(str, Enum):
    EXACT = "exact"
    SIMILAR = "similar"


class MatchStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SKIPPED = "skipped"
    APPLIED = "applied"
    FAILED = "failed"


class ConfidenceBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(slots=True)
class ScopeFilter:
    include_globs: list[str] = field(default_factory=lambda: ["**/*"])
    exclude_globs: list[str] = field(
        default_factory=lambda: [
            "**/.git/**",
            "**/.venv/**",
            "**/venv/**",
            "**/node_modules/**",
            "**/__pycache__/**",
            "**/dist/**",
            "**/build/**",
            "**/*.lock",
            "**/*.png",
            "**/*.jpg",
            "**/*.jpeg",
            "**/*.gif",
            "**/*.pdf",
            "**/*.zip",
            "**/*.exe",
            "**/*.dll",
            "**/*.so",
            "**/*.bin",
        ]
    )
    file_extensions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ChangeRequest:
    source_text: str
    target_text: str
    root_dir: Path
    scope: ScopeFilter = field(default_factory=ScopeFilter)
    similar_threshold: float = 0.78
    medium_threshold: float = 0.62
    low_threshold: float = 0.45
    created_by: str = "unknown"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass(slots=True)
class MatchItem:
    id: str
    file_path: str
    line_start: int
    line_end: int
    match_type: MatchType
    confidence: float
    confidence_band: ConfidenceBand
    before_snippet: str
    after_preview: str
    status: MatchStatus = MatchStatus.PENDING
    reason: str = ""
    source_fragment: str = ""
    replacement_fragment: str = ""


@dataclass(slots=True)
class OverviewStats:
    total_found: int
    file_count: int
    by_dir: dict[str, int]
    by_type: dict[str, int]
    by_band: dict[str, int]


@dataclass(slots=True)
class Stage1Decision:
    action: str
    comment: str = ""


@dataclass(slots=True)
class EditLogEntry:
    match_id: str
    file_path: str
    line_start: int
    line_end: int
    before: str
    after: str
    confirmed_by: str
    confirmed_at: str
    apply_at: str
    result: str
    message: str = ""


@dataclass(slots=True)
class RunReport:
    request: ChangeRequest
    total_found: int
    total_approved: int
    total_applied: int
    total_skipped: int
    total_failed: int
    residual_matches: int
    overview: OverviewStats
    entries: list[EditLogEntry]
    failures: list[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": {
                "source_text": self.request.source_text,
                "target_text": self.request.target_text,
                "root_dir": str(self.request.root_dir),
                "scope": {
                    "include_globs": self.request.scope.include_globs,
                    "exclude_globs": self.request.scope.exclude_globs,
                    "file_extensions": self.request.scope.file_extensions,
                },
                "created_by": self.request.created_by,
                "created_at": self.request.created_at,
            },
            "totals": {
                "found": self.total_found,
                "approved": self.total_approved,
                "applied": self.total_applied,
                "skipped": self.total_skipped,
                "failed": self.total_failed,
                "residual_matches": self.residual_matches,
            },
            "overview": {
                "total_found": self.overview.total_found,
                "file_count": self.overview.file_count,
                "by_dir": self.overview.by_dir,
                "by_type": self.overview.by_type,
                "by_band": self.overview.by_band,
            },
            "entries": [asdict(entry) for entry in self.entries],
            "failures": self.failures,
            "generated_at": self.generated_at,
        }

