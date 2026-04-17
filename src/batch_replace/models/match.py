"""匹配相关数据模型"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Position:
    """文本位置信息"""

    line: int  # 行号（从1开始）
    column: int  # 列号（从1开始）
    start: int  # 在文件中的起始偏移量
    end: int  # 在文件中的结束偏移量


@dataclass
class MatchInfo:
    """单个匹配信息"""

    position: Position
    matched_text: str
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)


@dataclass
class FileMatches:
    """单个文件的匹配结果"""

    file_path: Path
    matches: List[MatchInfo] = field(default_factory=list)

    @property
    def match_count(self) -> int:
        return len(self.matches)


@dataclass
class LocatedMatch:
    """定位后的匹配信息（包含完整上下文）"""

    file_path: Path
    line: int
    column: int
    target_text: str
    context_before: List[str]  # 前面几行
    target_line: str  # 匹配所在行
    context_after: List[str]  # 后面几行
    match_index: int = 0  # 在文件中的第几个匹配
    total_matches_in_file: int = 1
    position: Optional[Position] = None  # 完整位置信息（包含start/end偏移量）

    @property
    def display_position(self) -> str:
        return f"{self.file_path}:{self.line}:{self.column}"

    def get_preview(self, replacement: str) -> str:
        """生成修改预览"""
        return f"{self.target_line.replace(self.target_text, f'[[{replacement}]]')}"
