# AGENTS.md — PanelAgent

流式细胞多色 panel 设计工具。LLM + 确定性算法混合架构，正在向 SQLite 内核迁移。

## 必读（按顺序）

1. `docs/panelagent-core.md` — 内核包公开 API、schema、CLI/MCP 用法（权威文档）
2. `.agents/skills/panelagent-kernel/SKILL.md` — 架构不可变约束 + 已知坑（改 `panelagent/` 前必读）
3. `.agents/skills/panelagent-workflow/SKILL.md` — 任务派发/验收流程（接手编排任务必读）
4. `.agents/skills/panelagent-data-ops/SKILL.md` — 数据初始化与维护（动 config/ 或 CSV 必读）

## 快速事实

- **架构**：`panelagent/`（SQLite 内核包：CLI `pa` + MCP server + Python API）← FastAPI backend（Phase 2 接入中）← Next.js 前端
- **DB**：SQLite WAL，路径 `--db` > `PANELAGENT_DB` > `~/.local/share/panelagent/panelagent.db`；一个 DB = 一个实验室（多抗体库 + 多仪器）
- **切面分离**：backend 可 import panelagent 内核模块，禁止 import panelagent.cli/mcp；反向亦然
- **验证基线**：`PYTHONPATH=. python3 -m pytest tests/ -q`（≥312 passed）+ `ruff check`
- **git 政策**：不主动 commit，等用户点头

## 当前状态（2026-09-04）

- v0.1–v0.1.3 内核完成（未 commit）：`panelagent/` + `tests/core/`
- Phase 2 任务书就绪：`docs/refactor/phase2-backend.md`
- 历史任务书：`docs/refactor/`

## 常用命令

```bash
make test-backend          # pytest
make lint-backend          # ruff
make typecheck-frontend    # tsc
make generate-client && make check-drift   # OpenAPI 客户端同步检查
pa init --config-dir config --inventory-dir antibody_vault
pa panel generate --library Mouse --markers CD3,CD4,CD8 --json
```

## 注意

- frontend 用 Next.js 16（较新），写代码前查 `frontend/node_modules/next/dist/docs/`
- 内核相关历史坑（NULL target crash、mcp 1.x/2.x 兼容、亮度宁缺毋滥）见 `panelagent-kernel` skill，不在这里重复