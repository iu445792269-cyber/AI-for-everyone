"""文件工具函数"""

import fnmatch
import re
from pathlib import Path
from typing import List, Optional, Set

import chardet


class FileUtils:
    """文件工具类"""

    # 二进制文件扩展名列表
    BINARY_EXTENSIONS = {
        ".exe", ".dll", ".so", ".dylib", ".bin",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg",
        ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv",
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".db", ".sqlite", ".sqlite3",
    }

    @classmethod
    def is_binary_file(cls, file_path: Path) -> bool:
        """检查是否为二进制文件"""
        return file_path.suffix.lower() in cls.BINARY_EXTENSIONS

    @classmethod
    def is_hidden_file(cls, file_path: Path) -> bool:
        """检查是否为隐藏文件"""
        # Unix 隐藏文件
        if file_path.name.startswith("."):
            return True
        # Windows 隐藏文件（简化检查）
        return False


def detect_encoding(file_path: Path) -> str:
    """检测文件编码"""
    with open(file_path, "rb") as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result.get("encoding") or "utf-8"


def collect_files(
    scope: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    skip_binary: bool = True,
    skip_hidden: bool = True,
) -> List[Path]:
    """
    收集指定范围内的文件

    Args:
        scope: 搜索范围目录
        include_patterns: 包含的文件模式（如 ["*.md", "*.txt"]）
        exclude_patterns: 排除的文件/目录模式
        skip_binary: 是否跳过二进制文件
        skip_hidden: 是否跳过隐藏文件

    Returns:
        符合条件的文件路径列表
    """
    files = []
    exclude_patterns = exclude_patterns or []

    # 将 exclude_patterns 分为目录模式和普通模式
    dir_excludes = [p for p in exclude_patterns if p.endswith("/")]
    file_excludes = [p for p in exclude_patterns if not p.endswith("/")]

    for file_path in scope.rglob("*"):
        if not file_path.is_file():
            continue

        # 检查是否在排除的目录中
        rel_path = file_path.relative_to(scope)
        should_exclude = False

        for dir_pattern in dir_excludes:
            dir_pattern = dir_pattern.rstrip("/")
            if any(part.startswith(dir_pattern) or fnmatch.fnmatch(part, dir_pattern)
                   for part in rel_path.parts[:-1]):
                should_exclude = True
                break

        if should_exclude:
            continue

        # 检查是否为隐藏文件
        if skip_hidden and FileUtils.is_hidden_file(file_path):
            continue

        # 检查是否为二进制文件
        if skip_binary and FileUtils.is_binary_file(file_path):
            continue

        # 检查文件排除模式
        if any(fnmatch.fnmatch(file_path.name, pattern) for pattern in file_excludes):
            continue

        # 检查包含模式
        if include_patterns:
            if not any(fnmatch.fnmatch(file_path.name, pattern) for pattern in include_patterns):
                continue

        files.append(file_path)

    return sorted(files)


def find_line_column(content: str, offset: int) -> tuple[int, int]:
    """
    根据偏移量计算行号和列号

    Args:
        content: 文件内容
        offset: 字符偏移量

    Returns:
        (行号, 列号)，从1开始计数
    """
    lines = content[:offset].split("\n")
    line = len(lines)
    column = len(lines[-1]) + 1 if lines else 1
    return line, column
