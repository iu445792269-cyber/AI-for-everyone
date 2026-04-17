"""备份管理模块"""

import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


class BackupManager:
    """备份管理器"""

    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or Path.home() / ".batch_replace_backups"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]
        self.session_backup_dir = self.backup_dir / self.session_id
        self.session_backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, file_path: Path) -> Path:
        """
        为文件创建备份

        Args:
            file_path: 原文件路径

        Returns:
            备份文件路径
        """
        # 保留目录结构
        rel_path = file_path.name
        backup_path = self.session_backup_dir / rel_path

        # 处理重名
        counter = 1
        original_backup_path = backup_path
        while backup_path.exists():
            backup_path = original_backup_path.with_suffix(f".bak{counter}")
            counter += 1

        shutil.copy2(file_path, backup_path)
        return backup_path

    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        从备份恢复文件

        Args:
            backup_path: 备份文件路径
            target_path: 目标恢复路径

        Returns:
            是否成功
        """
        try:
            shutil.copy2(backup_path, target_path)
            return True
        except Exception:
            return False

    def cleanup_session(self) -> None:
        """清理本次会话的备份"""
        if self.session_backup_dir.exists():
            shutil.rmtree(self.session_backup_dir)

    def list_backups(self) -> list[Path]:
        """列出所有备份文件"""
        return list(self.session_backup_dir.rglob("*"))
