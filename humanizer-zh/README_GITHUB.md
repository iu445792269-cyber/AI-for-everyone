# Batch Edit Agent

安全优先的批量文本替换工具，提供：

- 精确匹配 + 近似匹配（带置信度分级）
- 两阶段人工确认（总览审批 + 逐条审批）
- 仅对已批准项应用修改
- 文件级原子回滚
- 执行日志与可审计报告

## 1. 项目结构

```text
batch_edit_agent/
  contracts.py
  search_layer.py
  review_layer.py
  apply_layer.py
  workflow.py
  cli.py
tests/
.github/workflows/ci.yml
pyproject.toml
```

## 2. 环境要求

- Python 3.10+

## 3. 本地安装

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
```

## 4. 快速运行

```bash
python -m batch_edit_agent.cli \
  --source "原句A" \
  --target "新句B" \
  --root "." \
  --include "docs/**/*.md,config/**/*.yml" \
  --ext ".md,.yml"
```

运行结束后默认输出：

- `reports/batch-edit-report.json`

## 5. 交互说明

- Stage 1（总览）：`approve_all` / `exact_only` / `revise`
- Stage 2（逐条）：`approve` / `skip` / `edit`

## 6. 开发与测试

```bash
python -m compileall batch_edit_agent
python -m pytest
```

## 7. 报告字段

报告包含：

- 请求参数（源句、新句、过滤范围、创建人）
- 总体统计（found/approved/applied/skipped/failed/residual）
- 目录与风险分布
- 每条执行日志（确认人、确认时间、改前改后、应用时间、结果）
- 失败信息

## 8. 发布到 GitHub 建议

1. 修改 `pyproject.toml` 中 `project.urls` 为你的仓库地址
2. 检查 `LICENSE`、`README_GITHUB.md`、`.github/workflows/ci.yml`
3. 推送仓库并启用 GitHub Actions

