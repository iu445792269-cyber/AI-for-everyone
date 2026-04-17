# Batch Edit Agent Workflow

This package provides a safe batch replacement workflow:

- exact + similar search with confidence bands
- stage-1 overview approval and stage-2 per-item review
- approved-only apply with per-file rollback
- residual check and JSON audit report

## Local dev

```bash
python -m pip install -e .
python -m compileall batch_edit_agent
python -m pytest
```

## Quick run

```bash
python -m batch_edit_agent.cli \
  --source "A" \
  --target "B" \
  --root "." \
  --include "docs/**/*.md,config/**/*.yml" \
  --ext ".md,.yml"
```

Default report path: `reports/batch-edit-report.json`.

