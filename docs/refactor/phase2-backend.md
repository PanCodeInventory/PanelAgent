# Phase 2 — 后端接入 panelagent 内核（读路径切换 + pa serve）

你负责 Phase 2。前置：v0.1 已完成（`panelagent/` 包存在，`PYTHONPATH=. python3 -m pytest tests/core -q` 全绿）。动工前先读 `docs/panelagent-core.md` 与 `docs/refactor/phase1-core.md`。

## 背景

FastAPI 后端（backend/app）目前直接读静态 JSON/CSV。v0.1 交付了独立内核包 panelagent（SQLite + CLI + MCP）。设计决定（已与用户拍板）：

- **没有独立质量注册表**。质量信息在 `antibodies.quality_flag / quality_notes / quality_updated_at` 列上。现有 quality_registry 体系（quality_registry_store、admin 质量端点、前端 quality-registry 页面）将被这套简化模型取代。
- **没有 panels 表、没有 audit_events**（panel 历史去留见下）。
- LLM 设置只读自 env（commit 676a087），不动。

## 目标

后端所有仪器/抗体/染料数据的读访问改走内核 SQLite；质量注册表替换为库存行内质量字段；提供 `pa serve` 变体。

## 交付物

### 1. 配置与启动

- `backend/app/main.py` lifespan：确保 schema + 空 DB 自动 seed（调 panelagent seed/import 接口，从仓库 `config/` + `inventory/`），日志打印条数。DB 路径解析与内核一致：`PANELAGENT_DB` env > 默认 `~/.local/share/panelagent/panelagent.db`。
- `backend/app/core/config.py`：删除 `CHANNEL_MAPPING_FILE / BRIGHTNESS_MAPPING_FILE / SPECTRAL_DATA_FILE / INVENTORY_DIR / SPECIES_INVENTORY_MAP`，保留 LLM/CORS。所有引用处迁移。
- 兼容旧数据：一次性迁移脚本（不进内核）`scripts/migrate_quality_registry.py`——把现有 JSON 质量注册表（quality_registry_store 的存储文件）按 target+clone 定位抗体行，写入 quality_flag/quality_notes。找不到对应行则打印清单让人工处理，不静默丢弃。

### 2. 数据访问层

（v0.1.1 起内核用 `antibodies.library` 列——任意库名 Mouse/Human/Isotype/…。backend API 对外参数如仍叫 species，一律映射到 library 过滤，不改对外契约。）

新建 `backend/app/services/kernel.py`：`get_kernel_conn()`（FastAPI Depends，线程安全：thread-local 或每请求短连接，防 SQLite locked）。逐个改造：

- `inventory.py` / `inventory_loader.py` → `antibodies` 表（library/target/keyword 过滤）。
- `spectra.py` → `fluorochrome_spectra` + `fluorochrome_brightness` 合并，响应形状不变。
- `panels.py` / `recommendations.py` 的 `_resolve_inventory_path` / `_load_inventory_df` / pandas 用法 → 查 `antibodies` 表。**panel_generator.py 接受 DataFrame 就喂 DataFrame**（列名 Target/Fluorescein/Clone/Brand/Catalog Number 一致），panel_generator.py 本身不改。
- `panel_history_store.py` → 评估历史改存 SQLite（内核无 panels 表，后端可自建 `panel_history` 表于同一 DB，schema 自定，payload 形状不变）。
- `quality_registry_store.py` / `quality_projection.py` / `quality_context_formatter.py` → 重写为基于 antibodies 质量列：quality 上下文 = 查涉及抗体的 flag/notes。**前端 quality-registry 页面行为会变**（从独立注册表变为库存行质量视图）——这是设计决定，不是回归；前端改动属于 Phase 3，先保证 API 不 500。
- `admin_database.py` / admin 质量端点：admin auth 保留；admin 质量管理端点改为改 antibodies 质量列。
- `settings.py` / `llm_settings_store.py`：不动（LLM 只读 env）。

### 3. pa serve

`panelagent/cli.py` 的 `pa serve`：真实启动 backend——`uvicorn.run("backend.app.main:app", ...)` 透传 --host/--port/--reload，DB 路径按内核规则注入 PANELAGENT_DB。切面分离：backend 可 import panelagent 内核模块（db/repo/engine/resolve），**禁止** import panelagent.cli / panelagent.mcp。

### 4. tests

- conftest fixture 换临时 DB；现有测试适配（质量注册表相关测试按新模型重写断言）。
- 新增 `tests/api/test_kernel_integration.py`：临时 DB + seed，TestClient 验证 inventory/spectra/panels/history 各端点形状。
- `make test-backend`、`make lint-backend`（ruff）绿。

### 验收（自己全部跑通再收工）

1. `make test-backend` 全绿；`make lint-backend` 干净
2. `make generate-client && make check-drift` 通过或证明 OpenAPI 无变化
3. `make typecheck-frontend` 通过
4. 手工冒烟：临时 DB 起 uvicorn，curl `/api/v1/inventory?species=Mouse`、`/api/v1/spectra` 200 且非空（贴输出）
5. `grep -rn 'channel_mapping.json\|spectral_data.json\|fluorochrome_brightness.json\|SPECIES_INVENTORY_MAP\|INVENTORY_DIR' backend/` 无残留（pycache 除外）
6. `pa serve` 起得来（curl health 200，贴输出）
7. `docs/panelagent-core.md` 尾部加 Phase 2 一节：改动文件、fixture 换法、pa serve 用法、迁移脚本用法

完成后输出：改动文件清单 + 验收命令实际输出摘要。
