"""定位Agent - 精确定位匹配内容并提取上下文"""

from pathlib import Path
from typing import List

from ..models.match import FileMatches, LocatedMatch, MatchInfo, Position
from ..utils.file_utils import detect_encoding


class LocateAgent:
    """定位Agent - 精确定位匹配内容在文件中的位置"""

    CONTEXT_LINES = 3  # 上下文行数

    def locate_all(self, file_matches: List[FileMatches]) -> List[LocatedMatch]:
        """
        定位所有匹配项

        Args:
            file_matches: 文件匹配结果列表

        Returns:
            定位后的匹配信息列表
        """
        located_matches = []

        for file_match in file_matches:
            for i, match in enumerate(file_match.matches):
                located = self._locate_single(file_match.file_path, match, i, len(file_match.matches))
                located_matches.append(located)

        return located_matches

    def _locate_single(
        self, file_path: Path, match: MatchInfo, index: int, total: int
    ) -> LocatedMatch:
        """
        定位单个匹配项

        Args:
            file_path: 文件路径
            match: 匹配信息
            index: 在文件中的匹配索引
            total: 文件中的总匹配数

        Returns:
            定位后的匹配信息
        """
        try:
            encoding = detect_encoding(file_path)
            lines = file_path.read_text(encoding=encoding).split("\n")
        except Exception as e:
            lines = [f"[读取文件失败: {e}]"]

        line_idx = match.position.line - 1

        # 提取上下文
        context_start = max(0, line_idx - self.CONTEXT_LINES)
        context_end = min(len(lines), line_idx + self.CONTEXT_LINES + 1)

        context_before = lines[context_start:line_idx]
        target_line = lines[line_idx] if line_idx < len(lines) else ""
        context_after = lines[line_idx + 1 : context_end]

        return LocatedMatch(
            file_path=file_path,
            line=match.position.line,
            column=match.position.column,
            target_text=match.matched_text,
            context_before=context_before,
            target_line=target_line,
            context_after=context_after,
            match_index=index,
            total_matches_in_file=total,
            position=match.position,
        )
