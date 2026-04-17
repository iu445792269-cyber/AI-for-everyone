"""检索Agent - 负责扫描文件并检索目标文本"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator, List, Optional

from ..models.match import FileMatches, MatchInfo, Position
from ..utils.file_utils import collect_files, detect_encoding, find_line_column


class MatchMode(Enum):
    """匹配模式"""

    EXACT = "exact"  # 精确匹配
    REGEX = "regex"  # 正则匹配
    WHOLE_WORD = "whole_word"  # 全词匹配


@dataclass
class SearchConfig:
    """搜索配置"""

    match_mode: MatchMode = MatchMode.EXACT
    case_sensitive: bool = False
    include_patterns: Optional[List[str]] = field(default_factory=lambda: ["*.md", "*.txt", "*.docx"])
    exclude_patterns: Optional[List[str]] = field(default_factory=lambda: [".git/", "node_modules/"])
    skip_binary: bool = True
    skip_hidden: bool = True
    max_matches_per_file: int = 50
    max_total_matches: int = 200


class SearchAgent:
    """检索Agent - 负责在指定范围内搜索目标文本"""

    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()

    def search(self, target: str, scope: Path) -> FileMatches:
        """
        在指定范围内搜索目标文本

        Args:
            target: 要查找的文本
            scope: 搜索范围路径

        Returns:
            FileMatches: 匹配结果列表
        """
        # 收集目标文件
        files = collect_files(
            scope=scope,
            include_patterns=self.config.include_patterns,
            exclude_patterns=self.config.exclude_patterns,
            skip_binary=self.config.skip_binary,
            skip_hidden=self.config.skip_hidden,
        )

        all_matches = []
        total_matches = 0

        for file_path in files:
            if total_matches >= self.config.max_total_matches:
                break

            matches = self._search_in_file(file_path, target)
            if matches:
                all_matches.append(FileMatches(file_path=file_path, matches=matches))
                total_matches += len(matches)

        return all_matches

    def _search_in_file(self, file_path: Path, target: str) -> List[MatchInfo]:
        """
        在单个文件中搜索目标文本

        Args:
            file_path: 文件路径
            target: 目标文本

        Returns:
            匹配信息列表
        """
        try:
            encoding = detect_encoding(file_path)
            content = file_path.read_text(encoding=encoding)
        except Exception:
            return []

        matches = []
        search_func = self._get_search_func()

        for match in search_func(content, target):
            start_pos = match.start()
            end_pos = match.end()
            line, column = find_line_column(content, start_pos)
            position = Position(
                line=line,
                column=column,
                start=start_pos,
                end=end_pos,
            )

            # 获取上下文
            lines = content.split("\n")
            context_before = lines[max(0, line - 4) : line - 1]
            context_after = lines[line : min(len(lines), line + 3)]

            matches.append(
                MatchInfo(
                    position=position,
                    matched_text=content[start_pos:end_pos],
                    context_before=context_before,
                    context_after=context_after,
                )
            )

            if len(matches) >= self.config.max_matches_per_file:
                break

        return matches

    def _get_search_func(self):
        """获取搜索函数"""
        if self.config.match_mode == MatchMode.REGEX:
            return self._regex_search
        elif self.config.match_mode == MatchMode.WHOLE_WORD:
            return self._whole_word_search
        else:
            return self._exact_search

    def _exact_search(self, content: str, target: str) -> Iterator[re.Match]:
        """精确匹配搜索"""
        flags = 0 if self.config.case_sensitive else re.IGNORECASE
        pattern = re.escape(target)
        return re.finditer(pattern, content, flags)

    def _regex_search(self, content: str, pattern: str) -> Iterator[re.Match]:
        """正则匹配搜索"""
        flags = 0 if self.config.case_sensitive else re.IGNORECASE
        return re.finditer(pattern, content, flags)

    def _whole_word_search(self, content: str, target: str) -> Iterator[re.Match]:
        """全词匹配搜索"""
        flags = 0 if self.config.case_sensitive else re.IGNORECASE
        pattern = r"\b" + re.escape(target) + r"\b"
        return re.finditer(pattern, content, flags)
