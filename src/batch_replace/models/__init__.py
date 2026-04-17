"""数据模型模块"""

from .match import MatchInfo, FileMatches, LocatedMatch, Position
from .change import ChangeRecord, ModifyTask, ChangePreview
from .result import SearchResult, ExecuteResult, RollbackResult

__all__ = [
    "MatchInfo",
    "FileMatches",
    "LocatedMatch",
    "Position",
    "ChangeRecord",
    "ModifyTask",
    "ChangePreview",
    "SearchResult",
    "ExecuteResult",
    "RollbackResult",
]
