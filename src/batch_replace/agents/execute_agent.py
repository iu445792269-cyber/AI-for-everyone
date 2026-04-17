"""执行Agent - 执行实际的文件修改操作"""

from pathlib import Path
from typing import List, Optional

from ..models.change import ChangeRecord, ModifyTask
from ..models.match import Position
from ..models.result import ExecuteResult, RollbackResult
from ..utils.backup import BackupManager
from ..utils.file_utils import detect_encoding


class ExecuteAgent:
    """执行Agent - 执行文件修改并管理变更日志"""

    def __init__(self, backup_manager: Optional[BackupManager] = None):
        self.backup_manager = backup_manager or BackupManager()
        self.change_log: List[ChangeRecord] = []

    def execute(self, task: ModifyTask) -> ExecuteResult:
        """
        执行单个修改任务

        Args:
            task: 修改任务

        Returns:
            执行结果
        """
        try:
            # 1. 创建备份
            backup_path = self.backup_manager.create_backup(task.file_path)

            # 2. 读取文件内容
            encoding = detect_encoding(task.file_path)
            content = task.file_path.read_text(encoding=encoding)

            # 3. 验证匹配位置的内容是否未变
            start = task.position.start
            end = task.position.end
            actual_text = content[start:end]

            if actual_text != task.original_text:
                return ExecuteResult(
                    success=False,
                    error_message=f"位置内容已变化: 期望 '{task.original_text}', 实际 '{actual_text}'",
                )

            # 4. 执行替换
            modified_content = content[:start] + task.replacement_text + content[end:]

            # 5. 写入文件
            task.file_path.write_text(modified_content, encoding=encoding)

            # 6. 记录变更
            record = ChangeRecord(
                file_path=task.file_path,
                backup_path=backup_path,
                original=task.original_text,
                replacement=task.replacement_text,
                position=task.position,
            )
            self.change_log.append(record)

            return ExecuteResult(success=True, record=record)

        except Exception as e:
            return ExecuteResult(success=False, error_message=str(e))

    def rollback_all(self) -> RollbackResult:
        """
        回滚所有已执行的修改

        Returns:
            回滚结果
        """
        failed_records = []
        success_count = 0

        # 从后往前回滚
        for record in reversed(self.change_log):
            try:
                self.backup_manager.restore_backup(record.backup_path, record.file_path)
                success_count += 1
            except Exception:
                failed_records.append(record)

        return RollbackResult(
            success=len(failed_records) == 0,
            rolled_back_count=success_count,
            failed_records=failed_records,
        )

    def rollback_last(self) -> ExecuteResult:
        """回滚最后一次修改"""
        if not self.change_log:
            return ExecuteResult(success=False, error_message="没有可回滚的修改")

        last_record = self.change_log.pop()
        try:
            self.backup_manager.restore_backup(last_record.backup_path, last_record.file_path)
            return ExecuteResult(success=True, record=last_record)
        except Exception as e:
            return ExecuteResult(success=False, error_message=str(e))

    def get_change_log(self) -> List[ChangeRecord]:
        """获取变更日志"""
        return self.change_log.copy()
