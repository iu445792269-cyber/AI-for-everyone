"""CLI接口"""

import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console

from .agents.confirm_agent import Action, ConfirmAgent
from .agents.execute_agent import ExecuteAgent
from .agents.locate_agent import LocateAgent
from .agents.search_agent import MatchMode, SearchAgent, SearchConfig
from .models.change import ModifyTask
from .ui.console_ui import ConsoleUI
from .ui.reporter import Reporter
from .utils.backup import BackupManager


@click.command()
@click.argument("target", required=True)
@click.argument("replacement", required=True)
@click.option(
    "--scope",
    "-s",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
    help="搜索范围目录 (默认: 当前目录)",
)
@click.option(
    "--include",
    "-i",
    multiple=True,
    default=["*.md", "*.txt"],
    help="包含的文件模式 (可多次指定, 如: -i '*.md' -i '*.txt')",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    default=[".git/", "__pycache__/", "node_modules/", ".venv/", "venv/"],
    help="排除的文件/目录模式",
)
@click.option(
    "--regex",
    "-r",
    is_flag=True,
    help="使用正则表达式匹配",
)
@click.option(
    "--whole-word",
    "-w",
    is_flag=True,
    help="全词匹配",
)
@click.option(
    "--case-sensitive",
    "-c",
    is_flag=True,
    help="区分大小写",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="跳过确认直接执行 (危险!)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="仅预览不执行",
)
@click.option(
    "--backup-dir",
    type=click.Path(path_type=Path),
    help="备份目录",
)
@click.option(
    "--report",
    is_flag=True,
    help="生成报告文件",
)
@click.option(
    "--report-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="报告输出目录",
)
@click.version_option(version="0.1.0", prog_name="batch-replace")
def main(
    target: str,
    replacement: str,
    scope: Path,
    include: tuple,
    exclude: tuple,
    regex: bool,
    whole_word: bool,
    case_sensitive: bool,
    yes: bool,
    dry_run: bool,
    backup_dir: Optional[Path],
    report: bool,
    report_dir: Optional[Path],
):
    """
    批量修改体系文件工具

    示例:
        batch-replace "旧文本" "新文本"
        batch-replace "质量管理体系" "质量管控体系" --scope ./docs
        batch-replace "V\\d+\\.\\d+" "V2.0" --regex
    """
    console = Console()
    ui = ConsoleUI(console)
    ui.show_welcome()

    # 确定匹配模式
    match_mode = MatchMode.EXACT
    if regex:
        match_mode = MatchMode.REGEX
    elif whole_word:
        match_mode = MatchMode.WHOLE_WORD

    # 创建搜索配置
    config = SearchConfig(
        match_mode=match_mode,
        case_sensitive=case_sensitive,
        include_patterns=list(include),
        exclude_patterns=list(exclude),
    )

    # 步骤1: 搜索
    ui.show_info(f"正在搜索: [cyan]{target}[/]")
    ui.show_info(f"搜索范围: [dim]{scope.absolute()}[/]")

    search_agent = SearchAgent(config)
    with ui.create_progress("搜索文件中...") as progress:
        progress.add_task(description="搜索中...")
        file_matches_list = search_agent.search(target, scope)

    if not file_matches_list:
        ui.show_warning("未找到匹配项")
        return

    # 步骤2: 定位
    locate_agent = LocateAgent()
    located_matches = locate_agent.locate_all(file_matches_list)

    total_matches = len(located_matches)
    ui.show_info(f"找到 {len(file_matches_list)} 个文件，共 {total_matches} 处匹配")

    if dry_run:
        ui.show_matches_summary(located_matches)
        return

    # 步骤3: 整体确认
    confirm_agent = ConfirmAgent(console)
    if not yes:
        if not confirm_agent.confirm_batch(located_matches, target, replacement):
            ui.show_info("操作已取消")
            return

    # 步骤4: 逐条确认和执行
    backup_manager = BackupManager(backup_dir)
    execute_agent = ExecuteAgent(backup_manager)

    modified_count = 0
    skipped_count = 0
    error_count = 0
    skip_current_file = False
    current_file = None

    for i, match in enumerate(located_matches):
        # 跳过整个文件的处理
        if skip_current_file and match.file_path == current_file:
            skipped_count += 1
            continue

        skip_current_file = False
        current_file = match.file_path

        # 获取当前的替换文本
        current_replacement = replacement

        if not yes:
            result = confirm_agent.confirm_individual(
                match, current_replacement, i, total_matches
            )

            if result.action == Action.QUIT:
                ui.show_warning("用户取消操作，正在回滚...")
                rollback_result = execute_agent.rollback_all()
                if rollback_result.success:
                    ui.show_info(f"已回滚 {rollback_result.rolled_back_count} 处修改")
                else:
                    ui.show_error(f"回滚失败: {rollback_result.error_message}")
                return

            elif result.action == Action.SKIP:
                skipped_count += 1
                continue

            elif result.action == Action.SKIP_FILE:
                skip_current_file = True
                skipped_count += 1
                continue

            elif result.action == Action.CONFIRM and result.edited_replacement:
                current_replacement = result.edited_replacement

        # 执行修改
        task = ModifyTask(
            file_path=match.file_path,
            original_text=match.target_text,
            replacement_text=current_replacement,
            position=match.position,
            located_match=match,
        )

        result = execute_agent.execute(task)

        if result.success:
            modified_count += 1
            ui.show_success(f"已修改: {match.display_position}")
        else:
            error_count += 1
            ui.show_error(f"修改失败: {match.display_position} - {result.error_message}")

    # 步骤5: 显示总结
    confirm_agent.show_summary(modified_count, skipped_count, error_count)

    # 生成报告
    if report or report_dir:
        reporter = Reporter(report_dir)
        change_log = execute_agent.get_change_log()

        text_report = reporter.generate_text_report(change_log, target, replacement)
        json_report = reporter.generate_json_report(change_log, target, replacement)

        ui.show_info(f"文本报告已保存: {text_report}")
        ui.show_info(f"JSON报告已保存: {json_report}")

    if error_count == 0:
        ui.show_success("批量修改完成!")
    else:
        ui.show_warning(f"批量修改完成，但有 {error_count} 处失败")


if __name__ == "__main__":
    main()
