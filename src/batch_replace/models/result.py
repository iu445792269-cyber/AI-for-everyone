"""结果相关数据模型"""

from dataclasses import dataclass, field
from typing import List, Optional

from .change import ChangeRecord


@dataclass
class SearchResult:
    """搜索结果"""

    total_files: int
    total_matches: int
    file_matches: List  # type: ignore # List[FileMatches]
    search_time_ms: float

    @property
    def has_matches(self) -> bool:
        return self.total_matches > 0


@dataclass
class ExecuteResult:
    """执行结果"""

    success: bool
    record: Optional[ChangeRecord] = None
    error_message: Optional[str] = None


@dataclass
class RollbackResult:
    """回滚结果"""

    success: bool
    rolled_back_count: int = 0
    failed_records: List[ChangeRecord] = field(default_factory=list)
    error_message: Optional[str] = None
