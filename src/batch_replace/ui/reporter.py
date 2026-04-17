"""报告生成模块"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from ..models.change import ChangeRecord


class Reporter:
    """报告生成器"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_text_report(
        self,
        records: List[ChangeRecord],
        target: str,
        replacement: str,
    ) -> Path:
        """生成文本报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"batch_replace_report_{timestamp}.txt"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("批量修改报告\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"目标文本: {target}\n")
            f.write(f"替换文本: {replacement}\n")
            f.write(f"总修改数: {len(records)}\n\n")

            f.write("-" * 80 + "\n")
            f.write("详细变更记录:\n")
            f.write("-" * 80 + "\n\n")

            for i, record in enumerate(records, 1):
                f.write(f"[{i}] {record.file_path}\n")
                f.write(f"    位置: 第 {record.position.line} 行, 第 {record.position.column} 列\n")
                f.write(f"    时间: {record.timestamp.strftime('%H:%M:%S')}\n")
                f.write(f"    原始: {record.original}\n")
                f.write(f"    替换: {record.replacement}\n")
                f.write(f"    备份: {record.backup_path}\n\n")

        return report_path

    def generate_json_report(
        self,
        records: List[ChangeRecord],
        target: str,
        replacement: str,
    ) -> Path:
        """生成JSON报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"batch_replace_report_{timestamp}.json"

        report_data = {
            "generated_at": datetime.now().isoformat(),
            "target": target,
            "replacement": replacement,
            "total_changes": len(records),
            "records": [
                {
                    "file_path": str(record.file_path),
                    "backup_path": str(record.backup_path),
                    "line": record.position.line,
                    "column": record.position.column,
                    "original": record.original,
                    "replacement": record.replacement,
                    "timestamp": record.timestamp.isoformat(),
                }
                for record in records
            ],
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return report_path
