"""确认Agent - 负责与用户交互确认"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..models.change import ChangePreview
from ..models.match import LocatedMatch


class Action(Enum):
    """用户操作"""

    CONFIRM = "Y"  # 确认
    SKIP = "n"  # 跳过
    SKIP_FILE = "s"  # 跳过此文件
    QUIT = "q"  # 取消全部
    EDIT = "e"  # 编辑替换文本
    HELP = "?"  # 帮助
    MORE_CONTEXT = "m"  # 更多上下文


@dataclass
class ConfirmResult:
    """确认结果"""

    action: Action
    edited_replacement: Optional[str] = None  # 用户编辑后的替换文本


class ConfirmAgent:
    """确认Agent - 负责与用户交互确认修改"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def confirm_batch(self, located_matches: List[LocatedMatch], target: str, replacement: str) -> bool:
        """
        整体确认匹配报告

        Args:
            located_matches: 所有定位后的匹配项
            target: 目标文本
            replacement: 替换文本

        Returns:
            是否继续
        """
        total_matches = len(located_matches)
        files = set(m.file_path for m in located_matches)

        # 创建汇总表格
        table = Table(title="检索结果报告", show_header=True, header_style="bold cyan")
        table.add_column("序号", style="dim", width=4)
        table.add_column("文件路径", style="green")
        table.add_column("匹配数", style="yellow", justify="right")

        file_stats = {}
        for match in located_matches:
            file_path = str(match.file_path)
            file_stats[file_path] = file_stats.get(file_path, 0) + 1

        for i, (file_path, count) in enumerate(sorted(file_stats.items()), 1):
            table.add_row(str(i), file_path, str(count))

        self.console.print()
        self.console.print(Panel(
            f"[bold]目标文本:[/] {target}\n"
            f"[bold]替换文本:[/] {replacement}\n"
            f"[bold]找到:[/] {len(files)} 个文件, {total_matches} 处匹配",
            title="批量修改",
            border_style="blue",
        ))
        self.console.print(table)

        # 询问是否继续
        self.console.print()
        return Confirm.ask("是否进入逐条确认?", default=True)

    def confirm_individual(
        self,
        match: LocatedMatch,
        replacement: str,
        current_index: int,
        total: int,
    ) -> ConfirmResult:
        """
        逐条确认修改

        Args:
            match: 当前匹配项
            replacement: 替换文本
            current_index: 当前索引
            total: 总数

        Returns:
            确认结果
        """
        self.console.print()
        self.console.print(Panel(
            f"[{current_index + 1}/{total}] {match.file_path}\n"
            f"位置: 第 {match.line} 行, 第 {match.column} 列",
            title="待确认修改项",
            border_style="yellow",
        ))

        # 显示修改预览
        self._show_preview(match, replacement)

        # 询问操作
        self.console.print()
        self.console.print("[dim]Y - 确认修改 | n - 跳过 | s - 跳过此文件 | q - 取消全部 | ? - 帮助[/]")

        while True:
            choice = Prompt.ask(
                "请选择操作",
                choices=["Y", "n", "s", "q", "?", "e", "m"],
                default="Y",
                show_choices=False,
            )

            if choice == "?":
                self._show_help()
                continue
            elif choice == "e":
                new_replacement = Prompt.ask("请输入新的替换文本", default=replacement)
                return ConfirmResult(Action.CONFIRM, edited_replacement=new_replacement)
            elif choice == "m":
                self._show_more_context(match)
                continue
            elif choice == "Y":
                return ConfirmResult(Action.CONFIRM)
            elif choice == "n":
                return ConfirmResult(Action.SKIP)
            elif choice == "s":
                return ConfirmResult(Action.SKIP_FILE)
            elif choice == "q":
                if Confirm.ask("确定要取消全部操作吗? 已修改的将被回滚", default=False):
                    return ConfirmResult(Action.QUIT)
                continue

    def _show_preview(self, match: LocatedMatch, replacement: str) -> None:
        """显示修改预览"""
        self.console.print("[bold cyan]修改预览:[/]")

        # BEFORE
        self.console.print("[dim]BEFORE:[/]")
        for i, line in enumerate(match.context_before):
            line_num = match.line - len(match.context_before) + i
            self.console.print(f"  {line_num:4d} │ {line}")

        target_highlight = match.target_line.replace(
            match.target_text, f"[bold red]{match.target_text}[/]"
        )
        self.console.print(f"  {match.line:4d} │ {target_highlight}")

        for i, line in enumerate(match.context_after):
            line_num = match.line + i + 1
            self.console.print(f"  {line_num:4d} │ {line}")

        # AFTER
        self.console.print()
        self.console.print("[dim]AFTER:[/]")
        for i, line in enumerate(match.context_before):
            line_num = match.line - len(match.context_before) + i
            self.console.print(f"  {line_num:4d} │ {line}")

        modified_line = match.target_line.replace(
            match.target_text, f"[bold green]{replacement}[/]"
        )
        self.console.print(f"  {match.line:4d} │ {modified_line}")

        for i, line in enumerate(match.context_after):
            line_num = match.line + i + 1
            self.console.print(f"  {line_num:4d} │ {line}")

    def _show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
[bold]可用操作:[/]
  [green]Y[/] - 确认修改此项
  [yellow]n[/] - 跳过此项 (不修改)
  [yellow]s[/] - 跳过此文件的所有剩余匹配
  [red]q[/] - 取消全部操作并回滚已修改
  [cyan]e[/] - 编辑替换文本
  [cyan]m[/] - 显示更多上下文
  [dim]?[/] - 显示此帮助
        """
        self.console.print(Panel(help_text, title="帮助", border_style="dim"))

    def _show_more_context(self, match: LocatedMatch, extra_lines: int = 5) -> None:
        """显示更多上下文"""
        try:
            from ..utils.file_utils import detect_encoding

            encoding = detect_encoding(match.file_path)
            all_lines = match.file_path.read_text(encoding=encoding).split("\n")

            start = max(0, match.line - extra_lines - 1)
            end = min(len(all_lines), match.line + extra_lines)

            self.console.print(f"[dim]显示第 {start + 1} 行到第 {end} 行:[/]")
            for i in range(start, end):
                prefix = ">>> " if i == match.line - 1 else "    "
                self.console.print(f"{prefix}{i + 1:4d} │ {all_lines[i]}")
        except Exception as e:
            self.console.print(f"[red]无法读取更多上下文: {e}[/]")

    def show_summary(self, modified: int, skipped: int, errors: int) -> None:
        """显示修改总结"""
        self.console.print()
        self.console.print(Panel(
            f"[green]成功修改: {modified} 处[/]\n"
            f"[yellow]跳过: {skipped} 处[/]\n"
            f"[red]错误: {errors} 处[/]",
            title="修改总结",
            border_style="green" if errors == 0 else "yellow",
        ))
