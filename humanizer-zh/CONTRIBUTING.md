# Contributing

## Development setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
python -m pip install pytest
```

## Validation before PR

```bash
python -m compileall batch_edit_agent
python -m pytest
```

## Pull request checklist

- [ ] 新功能包含测试
- [ ] 报告结构变更已更新文档
- [ ] 无本地语法错误
- [ ] 不包含临时输出或敏感信息

