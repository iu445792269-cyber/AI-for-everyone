"""变更相关数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .match import Position


@dataclass
class ChangeRecord:
    """变更记录"""

    file_path: Path
    backup_path: Path
    original: str
    replacement: str
    position: Position
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModifyTask:
    """修改任务"""

    file_path: Path
    original_text: str
    replacement_text: str
    position: Position
    located_match: Optional["LocatedMatch"] = None  # type: ignore


@dataclass
class ChangePreview:
    """变更预览"""

    file_path: Path
    line: int
    column: int
    original_lines: List[str]  # 包含上下文的原始行
    modified_lines: List[str]  # 包含上下文的修改后行
    highlight_line_index: int  # 高亮行的索引

    def format_preview(self) -> str:
        """格式化预览输出"""
        result = []
        result.append("BEFORE:")
        for i, line in enumerate(self.original_lines):
            prefix = ">>> " if i == self.highlight_line_index else "    "
            result.append(f"{prefix}{line}")

        result.append("")
        result.append("AFTER:")
        for i, line in enumerate(self.modified_lines):
            prefix = ">>> " if i == self.highlight_line_index else "    "
            result.append(f"{prefix}{line}")

        return "\n".join(result)
