"""控制台UI"""

from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from ..models.change import ChangeRecord
from ..models.match import LocatedMatch


class ConsoleUI:
    """控制台UI - 处理所有控制台输出"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def show_welcome(self) -> None:
        """显示欢迎信息"""
        self.console.print(Panel(
            "[bold blue]Batch Replace Tool[/bold blue]\n"
            "智能批量修改体系文件工具",
            border_style="blue",
        ))

    def show_error(self, message: str) -> None:
        """显示错误信息"""
        self.console.print(f"[bold red]错误:[/] {message}")

    def show_warning(self, message: str) -> None:
        """显示警告信息"""
        self.console.print(f"[bold yellow]警告:[/] {message}")

    def show_info(self, message: str) -> None:
        """显示信息"""
        self.console.print(f"[dim]{message}[/]")

    def show_success(self, message: str) -> None:
        """显示成功信息"""
        self.console.print(f"[bold green]✓[/] {message}")

    def create_progress(self, description: str = "处理中...") -> Progress:
        """创建进度条"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )

    def show_file_list(self, files: List[Path], title: str = "文件列表") -> None:
        """显示文件列表"""
        table = Table(title=title, show_header=False)
        table.add_column("文件路径", style="green")

        for file in files:
            table.add_row(str(file))

        self.console.print(table)

    def show_matches_summary(self, matches: List[LocatedMatch]) -> None:
        """显示匹配项汇总"""
        files = set(str(m.file_path) for m in matches)

        self.console.print()
        self.console.print(f"[bold]找到 {len(files)} 个文件，共 {len(matches)} 处匹配[/]")

        # 按文件分组显示
        file_groups = {}
        for match in matches:
            file_path = str(match.file_path)
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(match)

        for file_path, file_matches in sorted(file_groups.items()):
            self.console.print(f"\n[cyan]{file_path}[/] ({len(file_matches)} 处)")
            for m in file_matches:
                self.console.print(f"  第 {m.line} 行: {m.target_line[:50]}...")

    def show_change_log(self, records: List[ChangeRecord]) -> None:
        """显示变更日志"""
        if not records:
            self.console.print("[dim]暂无变更记录[/]")
            return

        table = Table(title="变更日志")
        table.add_column("时间", style="dim")
        table.add_column("文件", style="cyan")
        table.add_column("位置", style="yellow")
        table.add_column("原始内容", style="red", max_width=30)
        table.add_column("替换为", style="green", max_width=30)

        for record in records:
            table.add_row(
                record.timestamp.strftime("%H:%M:%S"),
                str(record.file_path),
                f"{record.position.line}:{record.position.column}",
                record.original[:50],
                record.replacement[:50],
            )

        self.console.print(table)

    def confirm(self, message: str, default: bool = False) -> bool:
        """确认对话框"""
        from rich.prompt import Confirm

        return Confirm.ask(message, default=default, console=self.console)

    def prompt(self, message: str, default: Optional[str] = None) -> str:
        """输入对话框"""
        from rich.prompt import Prompt

        return Prompt.ask(message, default=default, console=self.console)
