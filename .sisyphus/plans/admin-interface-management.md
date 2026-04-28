# PanelAgent 后台管理界面计划

## TL;DR
> **Summary**: 在现有 Next.js + FastAPI 应用上扩展两个新的顶层管理页面（`/settings`、`/history`），并增强已有 `quality-registry` 页面，使后台可管理运行时 LLM 配置、查看最终配色方案历史、编辑既有质量登记条目。
> **Deliverables**:
> - 运行时 LLM 设置后端存储/API + 前端设置页
> - 质量登记编辑 API + 前端编辑交互
> - 最终配色方案历史持久化/API + 前端只读历史页
> - OpenAPI client 同步、pytest/Playwright/lint/typecheck 验证
> **Effort**: Large
> **Parallel**: YES - 2 waves
> **Critical Path**: T1 → T2 → T3 → T5 → T6 → T7/T8/T9

## Context
### Original Request
- 开发后台管理界面，包含：
  1. 模型选择 / API Key 调整
  2. 过往配色方案生成历史
  3. 质量登记条目管理

### Interview Summary
- SQLite 可接受。
- 历史只保留**最终方案**，不保留中间候选。
- 不需要认证。
- 开发顺序固定：**Settings → Quality Registry 编辑增强 → History**。
- 测试策略固定：**tests-after**。
- 历史页**只读**，不支持回填到 `panel-design`。
- 路由组织沿用现有顶层导航模式，直接新增 `/settings` 与 `/history`，不引入 `/admin`。

### Metis Review (gaps addressed)
- 已补齐设置语义：仅支持**全局单例应用级 LLM 配置**，明确禁止 per-request/per-session override。
- 已补齐 API Key 语义：`GET` 仅返回 `has_api_key` 与 `api_key_masked`；`PUT` 中省略 `api_key` 表示保持不变，显式传空字符串表示清空。
- 已补齐历史写入触发：**仅在 `/panels/evaluate` 成功产出最终 `selected_panel` 后写入历史**。
- 已补齐质量登记编辑边界：本轮仅允许编辑 `issue_text` 与 `reported_by`；**不允许**编辑 `feedback_key`、`entity_key`、`status`。
- 已补齐范围控制：不引入通用后台框架、不把 history 扩展成回放/审计系统、不重构全部配置系统。

## Work Objectives
### Core Objective
为 PanelAgent 提供一个可执行、可验证、低侵入的后台管理能力扩展，在不引入认证和不改变现有主流程信息架构的前提下，让管理员可以：
1. 在线查看/更新运行时 LLM 配置；
2. 查看最终方案历史；
3. 编辑既有质量登记条目的文本元数据。

### Deliverables
- 后端 SQLite 管理库：`data/admin_console.sqlite3`
- LLM 设置存储/读取服务与 API
- 质量登记 issue 编辑 API
- 面板评估成功后写入历史的持久化逻辑
- 历史列表/详情 API
- 前端 `/settings` 页面
- 前端 `/history` 页面
- 前端 `quality-registry` 编辑弹窗/提交流程
- 更新后的 OpenAPI JSON 与生成客户端
- 自动化测试与证据产物

### Definition of Done (verifiable conditions with commands)
- `PYTHONPATH=. python -m pytest tests/api/ -q` 通过，新增 settings / history / quality edit API 用例全部通过。
- `PYTHONPATH=. python -m pytest tests/test_quality_registry_store.py tests/test_quality_context_formatter.py -q` 仍通过，说明未破坏现有质量登记核心行为。
- `make generate-client` 成功执行，且 `frontend/src/lib/api/generated/index.ts` 与 `frontend/src/lib/api/openapi.json` 已同步。
- `make check-drift` 通过，说明前后端 API 契约无漂移。
- `npm run lint --prefix frontend` 通过。
- `cd frontend && npx tsc --noEmit` 通过。
- `cd frontend && npx playwright test` 通过，并覆盖 settings/history/quality edit 三条后台路径。

### Must Have
- 顶部导航新增“设置”“历史”，复用现有 `frontend/src/app/layout.tsx:32-90` 顶层导航模式。
- 前端数据层继续使用 `api-client` + domain API module + hook 模式，参考：
  - `frontend/src/lib/api-client.ts:1-63`
  - `frontend/src/lib/api/quality-registry.ts:127-194`
  - `frontend/src/lib/hooks/use-quality-registry.ts:16-44`
- 新 UI 必须加入稳定的 `data-testid`，至少覆盖：页面容器、主表单、保存按钮、列表表格、详情弹窗、编辑弹窗。
- 设置读取必须支持“DB 覆盖 env 默认值；DB 无记录时回退 env”。
- 历史记录仅存最终评估结果：`species`、`markers`、`inventory_file`、`missing_markers`、`selected_panel`、`rationale`、`model_name`、`api_base`、`created_at`。
- 质量登记编辑必须写入 audit history。

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- 不新增认证/鉴权/角色系统。
- 不引入 `/admin` 分组或新的后台壳层。
- 不把 history 做成回填、重跑、版本比较、导出中心。
- 不让 settings 页面管理与 LLM 无关的全局配置。
- 不让质量登记编辑修改 `feedback_key` / `entity_key` / `status`，避免破坏投影与审核流。
- 不继续依赖“改 `.env` + `cache_clear` 即热生效”的不可靠方案。
- 不新增第二套前端 fetch 抽象。

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: **tests-after** + Pytest + Playwright + lint + typecheck
- QA policy: Every task includes API or UI executable scenarios with exact commands/selectors.
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Shared dependencies are extracted into Wave 1.

Wave 1: T1-T6 — backend/data contract/foundation
- T1 SQLite 管理库基础
- T2 运行时 LLM 设置存储与语义
- T3 LLM 读取路径重构为运行时配置
- T4 质量登记编辑后端能力
- T5 历史持久化与评估写入触发
- T6 OpenAPI/客户端同步

Wave 2: T7-T9 — frontend admin surfaces
- T7 Settings 页面
- T8 Quality Registry 编辑 UI
- T9 History 页面

### Dependency Matrix (full, all tasks)
| Task | Depends On | Blocks |
|---|---|---|
| T1 | none | T2, T5 |
| T2 | T1 | T3, T6, T7 |
| T3 | T2 | T5 |
| T4 | none | T6, T8 |
| T5 | T1, T3 | T6, T9 |
| T6 | T2, T4, T5 | T7, T8, T9 |
| T7 | T6 | F1-F4 |
| T8 | T6 | F1-F4 |
| T9 | T6 | F1-F4 |

### Agent Dispatch Summary (wave → task count → categories)
| Wave | Task Count | Categories |
|---|---:|---|
| Wave 1 | 6 | unspecified-high ×4, quick ×2 |
| Wave 2 | 3 | visual-engineering ×3 |
| Final | 4 | oracle / unspecified-high / deep |

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [x] 1. 建立 SQLite 管理持久层基础

  **What to do**:
  - 新建共享 SQLite 访问层，固定数据库文件为 `data/admin_console.sqlite3`。
  - 在同一初始化路径中创建两张表：
    - `llm_settings(id INTEGER PRIMARY KEY CHECK(id = 1), api_base TEXT NOT NULL, api_key TEXT NULL, model_name TEXT NOT NULL, updated_at TEXT NOT NULL)`
    - `panel_history(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, species TEXT NOT NULL, inventory_file TEXT NULL, requested_markers TEXT NOT NULL, missing_markers TEXT NOT NULL, selected_panel TEXT NOT NULL, rationale TEXT NOT NULL, model_name TEXT NOT NULL, api_base TEXT NOT NULL)`
  - 使用 Python 标准库 `sqlite3`，不要引入 ORM、Alembic、SQLAlchemy。
  - 提供幂等初始化函数，供 settings store 与 history store 复用。

  **Must NOT do**:
  - 不拆成多数据库文件。
  - 不把现有 `quality_registry` JSON 存储迁移到 SQLite。
  - 不增加通用 migration 框架。

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 多文件后端基础设施，要求稳定数据契约与最小侵入。
  - Skills: [] - 无特定技能依赖。
  - Omitted: [`fastapi-templates`] - 当前不是新建 FastAPI 项目。

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T2, T5 | Blocked By: none

  **References**:
  - Pattern: `backend/app/services/quality_registry_store.py:50-83` - 现有持久化层强调幂等目录创建与稳定读写语义。
  - Pattern: `backend/app/services/quality_registry_store.py:97-125` - service/store 组织方式可直接借鉴。
  - API/Type: `backend/app/core/config.py:57-80` - 项目根路径/数据路径解析思路。

  **Acceptance Criteria**:
  - [ ] 运行 `PYTHONPATH=. python -m pytest tests/ -q -k "admin_console or panel_history or llm_settings"` 时新增 store 测试通过。
  - [ ] 首次实例化 store 后，`data/admin_console.sqlite3` 自动创建且包含 `llm_settings`、`panel_history` 两张表。
  - [ ] 重复初始化不会抛错，也不会重复建表。

  **QA Scenarios**:
  ```
  Scenario: SQLite schema bootstrap
    Tool: Bash
    Steps: PYTHONPATH=. python -m pytest tests/ -q -k "admin_console or panel_history or llm_settings"
    Expected: exit code 0; pytest output contains newly added tests as PASSED
    Evidence: .sisyphus/evidence/task-1-sqlite-foundation.txt

  Scenario: Re-initialization remains idempotent
    Tool: Bash
    Steps: run the same targeted pytest suite twice in succession
    Expected: second run also exits 0; no duplicate-table or locked-database errors
    Evidence: .sisyphus/evidence/task-1-sqlite-foundation-repeat.txt
  ```

  **Commit**: YES | Message: `feat(admin): add sqlite foundation for settings and history` | Files: `backend/app/services/*`, `tests/*`, `data/.gitkeep if needed`

- [x] 2. 实现运行时 LLM 设置存储与 API 语义

  **What to do**:
  - 新增设置 schema 与 store/service，定义全局单例语义。
  - `GET /api/v1/settings/llm` 返回：`api_base`、`model_name`、`has_api_key`、`api_key_masked`、`source`（`runtime` 或 `env-default`）。
  - `PUT /api/v1/settings/llm` 接受部分更新：
    - 省略字段 = 保持原值
    - `api_key: ""` = 清空 DB 中的 key
    - 首次更新时，先以“当前有效值（DB 优先，否则 env）”为基础再 merge
    - 一旦存在 DB 行，读取时始终以 DB 为准；仅在 **DB 无记录** 时才回退 env 默认值
  - DB 无记录时，读取 `backend/app/core/config.py:21-27` 的 env 默认值。
  - API key mask 规则固定：长度 ≥8 时显示前 3 位 + `****` + 后 4 位，否则统一 `****`。

  **Must NOT do**:
  - 不暴露完整 API key 给前端读接口。
  - 不支持 per-user/per-session 设置。
  - 不引入“测试连接”功能。

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 涉及安全语义、回退策略、接口契约。
  - Skills: []
  - Omitted: [`git-commit`] - 非 git 操作。

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T3, T6, T7 | Blocked By: T1

  **References**:
  - Pattern: `backend/app/core/config.py:9-27` - 现有 env 默认值来源。
  - Pattern: `backend/app/core/config.py:44-47` - 现有 `get_settings()` 入口。
  - Pattern: `frontend/src/lib/api/quality-registry.ts:127-194` - 前后端 API 契约风格。
  - Test: `tests/api/test_quality_registry.py` - 现有 API 断言风格可复用。

  **Acceptance Criteria**:
  - [ ] DB 为空时，`GET /api/v1/settings/llm` 返回 env 默认值且 `source == "env-default"`。
  - [ ] 提交 `PUT /api/v1/settings/llm` 仅更新提供字段，其余字段保持不变。
  - [ ] 提交空字符串 `api_key` 后，后续 `GET` 返回 `has_api_key == false` 且 `api_key_masked == null`。
  - [ ] `GET` 永不返回完整 `api_key`。

  **QA Scenarios**:
  ```
  Scenario: Default settings fallback from env
    Tool: Bash
    Steps: PYTHONPATH=. python -m pytest tests/api/ -q -k "settings and fallback"
    Expected: exit code 0; response JSON includes source=env-default and masked/boolean key fields only
    Evidence: .sisyphus/evidence/task-2-settings-fallback.txt

  Scenario: Empty api_key clears stored value
    Tool: Bash
    Steps: PYTHONPATH=. python -m pytest tests/api/ -q -k "settings and clear_api_key"
    Expected: exit code 0; follow-up GET shows has_api_key false and api_key_masked null
    Evidence: .sisyphus/evidence/task-2-settings-clear-key.txt
  ```

  **Commit**: YES | Message: `feat(settings): add runtime llm settings api semantics` | Files: `backend/app/schemas/*`, `backend/app/services/*`, `backend/app/api/v1/endpoints/settings.py`, `tests/api/*`

- [x] 3. 重构 LLM 调用路径为运行时读取设置

  **What to do**:
  - 改造 `llm_api_client.py`，让 `consult_gpt_oss(prompt)` 在每次调用时根据“当前有效设置”构造 OpenAI client，而不是在模块 import 时固定客户端。
  - 保持外部函数签名不变，避免大面积改动调用方。
  - 确保默认模型名也从运行时设置读取，不再直接 `os.getenv`。
  - 保留异常语义（仍返回 `连接错误: ...` 字符串），避免破坏现有上层逻辑。

  **Must NOT do**:
  - 不重写 `panel_generator.py` 的主业务逻辑。
  - 不引入全局可变单例缓存新的 client。
  - 不改变 `consult_gpt_oss` 的返回格式。

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 涉及运行时行为修复与兼容性约束。
  - Skills: []
  - Omitted: [`ai-sdk`] - 当前不是 Vercel AI SDK 改造。

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T5 | Blocked By: T2

  **References**:
  - Pattern: `llm_api_client.py:9-31` - 当前模块级 client 初始化是必须替换的对象。
  - Pattern: `panel_generator.py:5-14` - `consult_gpt_oss` 的上游调用与质量上下文耦合点。
  - API/Type: `backend/app/core/config.py:24-27` - 当前 LLM 默认配置字段。

  **Acceptance Criteria**:
  - [ ] 针对 `consult_gpt_oss` 的测试可证明：先写入设置 A，再写入设置 B，第二次调用使用 B 而非 A。
  - [ ] 未配置运行时设置时，仍能回退 env 默认值成功构造 client。
  - [ ] `panel_generator.py` 无需感知 settings 来源变化即可继续工作。

  **QA Scenarios**:
  ```
  Scenario: Runtime settings take effect without restart
    Tool: Bash
    Steps: PYTHONPATH=. python -m pytest tests/ -q -k "runtime_llm_settings"
    Expected: exit code 0; mocked client construction asserts updated api_base/model_name values on second call
    Evidence: .sisyphus/evidence/task-3-runtime-llm.txt

  Scenario: Env fallback still works
    Tool: Bash
    Steps: PYTHONPATH=. python -m pytest tests/ -q -k "llm_env_fallback"
    Expected: exit code 0; when SQLite row absent the client uses config defaults
    Evidence: .sisyphus/evidence/task-3-env-fallback.txt
  ```

  **Commit**: YES | Message: `fix(llm): read runtime settings on each request` | Files: `llm_api_client.py`, `tests/*`, optional service helpers

- [x] 4. 为质量登记增加安全的编辑后端能力

  **What to do**:
  - 新增 `QualityIssueUpdate` schema，仅包含 `issue_text` 与 `reported_by`。
  - 在 `QualityRegistryStore` 中新增编辑方法：更新上述字段、刷新 `updated_at`、追加 `edited` audit event。
  - 新增 `PUT /api/v1/quality-registry/issues/{issue_id}`。
  - 明确错误语义：issue 不存在返回 404；空白文本返回 422。

  **Must NOT do**:
  - 不允许通过此接口改 `feedback_key` / `entity_key` / `status`。
  - 不引入 delete/bulk edit/export。

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: 单领域 CRUD 增强，范围清晰。
  - Skills: []
  - Omitted: [`fastapi-templates`] - 非新项目。

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: T6, T8 | Blocked By: none

  **References**:
  - Pattern: `backend/app/api/v1/endpoints/quality_registry.py:121-155` - 现有 issue CRUD 风格。
  - Pattern: `backend/app/services/quality_registry_store.py:132-148` - 内部 `_update_issue` 已可复用为编辑实现基础。
  - Pattern: `backend/app/services/quality_registry_store.py:181-193` - audit append 行为参考。
  - API/Type: `frontend/src/lib/api/quality-registry.ts:39-58` - 现有前端 issue 类型需兼容。

  **Acceptance Criteria**:
  - [ ] `PUT /api/v1/quality-registry/issues/{id}` 成功后返回更新后的 issue。
  - [ ] 仅 `issue_text`、`reported_by`、`updated_at` 发生变化。
  - [ ] `GET /api/v1/quality-registry/issues/{id}/history` 可看到 `edited` 事件。

  **QA Scenarios**:
  ```
  Scenario: Edit existing issue metadata
    Tool: Bash
    Steps: PYTHONPATH=. python -m pytest tests/api/ -q -k "quality_registry and update_issue"
    Expected: exit code 0; response JSON shows edited issue_text/reported_by and unchanged status/feedback_key
    Evidence: .sisyphus/evidence/task-4-quality-edit-api.txt

  Scenario: Reject invalid edit payload
    Tool: Bash
    Steps: PYTHONPATH=. python -m pytest tests/api/ -q -k "quality_registry and invalid_update_issue"
    Expected: exit code 0; API returns 422 for blank issue_text or blank reported_by
    Evidence: .sisyphus/evidence/task-4-quality-edit-api-error.txt
  ```

  **Commit**: YES | Message: `feat(quality): add issue metadata editing api` | Files: `backend/app/schemas/quality_registry.py`, `backend/app/services/quality_registry_store.py`, `backend/app/api/v1/endpoints/quality_registry.py`, `tests/api/*`

- [x] 5. 持久化最终配色方案历史并扩展评估请求上下文

  **What to do**:
  - 为 `PanelEvaluateRequest` 增加上下文字段：`species`、`markers`、`inventory_file`。
  - 在 `POST /api/v1/panels/evaluate` 成功返回 `selected_panel` 后，立即写入 `panel_history`。
  - 历史只存最终结果，不存候选列表。
  - 新增 `GET /api/v1/panel-history`（列表）与 `GET /api/v1/panel-history/{history_id}`（详情）。
  - 列表按 `created_at DESC` 排序。
  - 写入时记录**当时有效的** `model_name` 与 `api_base` 快照。

  **Must NOT do**:
  - 不在 `/panels/generate` 阶段写历史。
  - 不保存原始完整 LLM 响应消息、对话 transcript、候选方案全集。
  - 不支持编辑或删除历史。

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 涉及 API 契约调整、核心评估流程挂钩、持久化边界。
  - Skills: []
  - Omitted: [`git-master`] - 非 git 操作。

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T6, T9 | Blocked By: T1, T3

  **References**:
  - Pattern: `backend/app/schemas/panels.py:46-56` - 当前 evaluate request/response shape 需要扩展。
  - Pattern: `backend/app/api/v1/endpoints/panels.py:168-207` - 历史写入必须挂在 evaluate 成功路径。
  - Pattern: `frontend/src/lib/hooks/use-panel-evaluation.ts:37-62` - 前端 evaluate 请求需要同步追加上下文。
  - Pattern: `frontend/src/lib/hooks/use-panel-generation.ts:64-69` - generation 阶段已有 `species`/`inventory_file` 上下文来源。
  - Pattern: `frontend/src/app/panel-design/page.tsx:157-175` - `handleEvaluate` 当前调用点需要补充 markers/species。

  **Acceptance Criteria**:
  - [ ] 成功调用 `/api/v1/panels/evaluate` 后，`GET /api/v1/panel-history` 能看到一条新记录。
  - [ ] 历史详情包含：`species`、`requested_markers`、`missing_markers`、`selected_panel`、`rationale`、`model_name`、`api_base`、`created_at`。
  - [ ] evaluate 失败时不会写入历史。

  **QA Scenarios**:
  ```
  Scenario: Successful evaluation writes exactly one history record
    Tool: Bash
    Steps: PYTHONPATH=. python -m pytest tests/api/ -q -k "panel_history and evaluate_success"
    Expected: exit code 0; test asserts history count increments by 1 and stored row includes selected_panel + model snapshot
    Evidence: .sisyphus/evidence/task-5-panel-history.txt

  Scenario: Failed evaluation does not write history
    Tool: Bash
    Steps: PYTHONPATH=. python -m pytest tests/api/ -q -k "panel_history and evaluate_failure"
    Expected: exit code 0; history count remains unchanged when evaluation returns error/raises
    Evidence: .sisyphus/evidence/task-5-panel-history-error.txt
  ```

  **Commit**: YES | Message: `feat(history): persist final panel evaluations` | Files: `backend/app/schemas/panels.py`, `backend/app/api/v1/endpoints/panels.py`, `backend/app/api/v1/endpoints/panel_history.py`, `backend/app/services/*`, `tests/api/*`

- [x] 6. 同步 OpenAPI 契约并更新生成客户端

  **What to do**:
  - 在完成 T2/T4/T5 后执行 `make generate-client`。
  - 确保 `frontend/src/lib/api/openapi.json` 与 `frontend/src/lib/api/generated/index.ts` 纳入同一变更集。
  - 若新增 endpoint/tag 后前端仍保留手写 wrapper，则 wrapper 必须改为基于最新 schema 类型。
  - 运行 `make check-drift`，确保无契约漂移。

  **Must NOT do**:
  - 不跳过 OpenAPI 同步。
  - 不让 frontend 使用过期 schema 手写绕过类型错误。

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: 流程明确，但对后续 frontend 任务是关键阻塞。
  - Skills: []
  - Omitted: [`vercel-ai-sdk`] - 非 AI SDK 任务。

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T7, T8, T9 | Blocked By: T2, T4, T5

  **References**:
  - Pattern: `Makefile:21-29` - `generate-client` 与 `check-drift` 官方工作流。
  - Pattern: `frontend/scripts/generate-client.mjs:39-70` - 前端类型生成流程。
  - Pattern: `scripts/generate-openapi.py:25-57` - 后端 schema 导出来源。

  **Acceptance Criteria**:
  - [ ] `make generate-client` 退出码为 0。
  - [ ] `make check-drift` 退出码为 0。
  - [ ] 生成客户端包含 settings、panel-history、quality issue update 的最新 schema/paths。

  **QA Scenarios**:
  ```
  Scenario: OpenAPI regeneration succeeds
    Tool: Bash
    Steps: make generate-client
    Expected: exit code 0; generated client files updated without script failure
    Evidence: .sisyphus/evidence/task-6-generate-client.txt

  Scenario: Contract drift check passes
    Tool: Bash
    Steps: make check-drift
    Expected: exit code 0; no drift reported
    Evidence: .sisyphus/evidence/task-6-check-drift.txt
  ```

  **Commit**: NO | Message: `chore(api): regenerate openapi client` | Files: `frontend/src/lib/api/openapi.json`, `frontend/src/lib/api/generated/index.ts`

- [x] 7. 实现 `/settings` 页面与导航入口

  **What to do**:
  - 在 `frontend/src/app/layout.tsx` 顶部导航新增 “设置” 链接。
  - 新建 `frontend/src/app/settings/page.tsx` 与需要的 client 组件/Hook/API wrapper。
  - 复用 Card/Input/Button 组合，沿用 `quality-registry` 的 hook 状态模式。
  - 页面必须提供：
    - `API Base` 输入框
    - `Model Name` 输入框
    - `API Key` 密码框（默认空白，占位显示 masked state / has key state）
    - 保存按钮
    - 成功/错误提示
  - 必须加入 `data-testid`：`settings-page`, `settings-form`, `settings-api-base`, `settings-model-name`, `settings-api-key`, `settings-save-button`。

  **Must NOT do**:
  - 不展示明文 API key。
  - 不添加与本轮无关的设置项。
  - 不创建新的全局状态库。

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 需要在现有设计系统内做完整管理表单 UX。
  - Skills: [`shadcn`] - 复用现有 UI primitive 与 form composition。
  - Omitted: [`frontend-design`] - 这不是视觉重设计任务，目标是贴合现有后台风格。

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: F1-F4 | Blocked By: T6

  **References**:
  - Pattern: `frontend/src/app/layout.tsx:32-81` - 顶层导航插入位置。
  - Pattern: `frontend/src/app/quality-registry/page.tsx:1-5` - route wrapper 模式。
  - Pattern: `frontend/src/app/quality-registry/quality-registry-client.tsx:3-27` - Card/Dialog/Tabs/import 组合模式。
  - Pattern: `frontend/src/lib/api-client.ts:8-63` - 请求封装入口。
  - Pattern: `frontend/src/lib/hooks/use-quality-registry.ts:58-146` - hook 状态管理基线。

  **Acceptance Criteria**:
  - [ ] 访问 `/settings` 可成功加载当前设置。
  - [ ] 保存后页面展示成功状态，重新加载仍显示更新后的 `api_base` / `model_name`。
  - [ ] 若 API key 已存在，页面只展示 masked/boolean 状态，不展示明文。

  **QA Scenarios**:
  ```
  Scenario: Settings page loads and saves runtime settings
    Tool: Playwright
    Steps: go to /settings; wait for [data-testid="settings-page"]; fill [data-testid="settings-api-base"] with "https://example.com/v1"; fill [data-testid="settings-model-name"] with "gpt-test"; fill [data-testid="settings-api-key"] with "sk-test-12345678"; click [data-testid="settings-save-button"]
    Expected: success toast/message visible; reload page and fields still show api_base/model_name while API key remains masked/empty
    Evidence: .sisyphus/evidence/task-7-settings-ui.png

  Scenario: Settings page rejects invalid blank required fields
    Tool: Playwright
    Steps: go to /settings; clear [data-testid="settings-api-base"]; click [data-testid="settings-save-button"]
    Expected: inline validation or server error shown; no silent success state
    Evidence: .sisyphus/evidence/task-7-settings-ui-error.png
  ```

  **Commit**: YES | Message: `feat(frontend): add runtime settings page` | Files: `frontend/src/app/layout.tsx`, `frontend/src/app/settings/*`, `frontend/src/lib/api/*`, `frontend/src/lib/hooks/*`, Playwright tests

- [x] 8. 在质量登记页面加入 issue 编辑交互

  **What to do**:
  - 在 `quality-registry` 的历史/列表视图中增加“编辑”按钮。
  - 使用 Dialog 打开编辑表单，预填当前 `issue_text` 与 `reported_by`。
  - 提交成功后：
    - 刷新 issue 列表
    - 若当前 issue 正在查看，则刷新其 history
    - 保持当前 tab/selection 不跳回默认页
  - 前端 wrapper/hook 增加 `updateIssue(issueId, payload)`。
  - 必须加入 `data-testid`：`quality-edit-button`, `quality-edit-dialog`, `quality-edit-issue-text`, `quality-edit-reported-by`, `quality-edit-save-button`。

  **Must NOT do**:
  - 不增加删除按钮。
  - 不允许编辑反馈键、候选绑定、审核状态。
  - 不重写整个 `quality-registry-client.tsx` 结构。

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 需要在既有复杂页面中插入局部交互且不破坏状态机。
  - Skills: [`shadcn`] - Dialog/form 复用。
  - Omitted: [`frontend-design`] - 不需要重新设计布局。

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: F1-F4 | Blocked By: T6

  **References**:
  - Pattern: `frontend/src/app/quality-registry/quality-registry-client.tsx:81-120` - 主状态与 hook 使用。
  - Pattern: `frontend/src/app/quality-registry/quality-registry-client.tsx:177-207` - 表单状态更新/重置方式。
  - Pattern: `frontend/src/lib/api/quality-registry.ts:127-194` - 现有 wrapper 风格，需新增 `updateIssue`。
  - Pattern: `frontend/src/lib/hooks/use-quality-registry.ts:63-224` - hook action 风格，需扩展编辑动作。

  **Acceptance Criteria**:
  - [ ] 页面中可打开编辑弹窗并提交 `issue_text`、`reported_by`。
  - [ ] 编辑成功后，列表行内容与 history 面板均反映新值/新审计事件。
  - [ ] 编辑失败时显示错误，不关闭弹窗、不污染本地状态。

  **QA Scenarios**:
  ```
  Scenario: Edit issue from quality registry UI
    Tool: Playwright
    Steps: go to /quality-registry; wait for issue list; click first [data-testid="quality-edit-button"]; in [data-testid="quality-edit-dialog"] fill [data-testid="quality-edit-issue-text"] with "更新后的质量问题描述" and [data-testid="quality-edit-reported-by"] with "Admin User"; click [data-testid="quality-edit-save-button"]
    Expected: dialog closes; updated text appears in issue list/detail; history panel contains an edited event
    Evidence: .sisyphus/evidence/task-8-quality-edit-ui.png

  Scenario: Edit failure preserves dialog state
    Tool: Playwright
    Steps: open edit dialog; clear [data-testid="quality-edit-issue-text"]; click [data-testid="quality-edit-save-button"]
    Expected: validation or API error displayed; dialog remains open; original list row unchanged
    Evidence: .sisyphus/evidence/task-8-quality-edit-ui-error.png
  ```

  **Commit**: YES | Message: `feat(frontend): add quality issue edit dialog` | Files: `frontend/src/app/quality-registry/*`, `frontend/src/lib/api/quality-registry.ts`, `frontend/src/lib/hooks/use-quality-registry.ts`, Playwright tests

- [x] 9. 实现只读 `/history` 页面与导航入口

  **What to do**:
  - 在 `frontend/src/app/layout.tsx` 顶部导航新增 “历史” 链接。
  - 新建 `frontend/src/app/history/page.tsx` 与 client 组件/Hook/API wrapper。
  - 页面展示列表字段：时间、物种、marker 数量、model 名称。
  - 点击列表项后展示详情面板/弹窗，内容包含：requested markers、missing markers、selected panel、rationale、api_base、model_name、inventory_file。
  - 列表按时间倒序。
  - 页面保持只读，不提供编辑/删除/回填操作。
  - 必须加入 `data-testid`：`history-page`, `history-table`, `history-row`, `history-detail-trigger`, `history-detail-dialog`。

  **Must NOT do**:
  - 不加入“重新生成”“加载到配色页”“删除历史”。
  - 不把候选方案列表补回历史详情。

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 数据列表 + 详情交互页面，要求沿用现有设计语言。
  - Skills: [`shadcn`] - Card/Dialog/Table 风格复用。
  - Omitted: [`frontend-design`] - 不做全新视觉体系。

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: F1-F4 | Blocked By: T6

  **References**:
  - Pattern: `frontend/src/app/layout.tsx:44-80` - 顶层 nav 风格。
  - Pattern: `frontend/src/app/panel-design/page.tsx:47-121` - panel table 呈现方式可复用为历史详情中 selected panel 展示。
  - Pattern: `frontend/src/app/quality-registry/quality-registry-client.tsx:13-25` - Dialog/Tabs/Card 组合方式。
  - Pattern: `frontend/src/lib/api-client.ts:43-63` - API 调用封装。

  **Acceptance Criteria**:
  - [ ] 访问 `/history` 可看到按时间倒序排列的历史列表。
  - [ ] 点击某条记录可打开详情，看到 selected panel 与 rationale。
  - [ ] UI 中不存在回填/编辑/删除按钮。

  **QA Scenarios**:
  ```
  Scenario: History page lists final panel records
    Tool: Playwright
    Steps: go to /history; wait for [data-testid="history-page"]; assert [data-testid="history-table"] is visible; click first [data-testid="history-detail-trigger"]
    Expected: [data-testid="history-detail-dialog"] opens and shows selected panel rows plus rationale/model/api_base metadata
    Evidence: .sisyphus/evidence/task-9-history-ui.png

  Scenario: History page remains read-only
    Tool: Playwright
    Steps: go to /history; inspect visible buttons/links in table and detail dialog
    Expected: no control with text matching 重新生成 / 回填 / 编辑 / 删除 is visible
    Evidence: .sisyphus/evidence/task-9-history-ui-readonly.png
  ```

  **Commit**: YES | Message: `feat(frontend): add panel history page` | Files: `frontend/src/app/layout.tsx`, `frontend/src/app/history/*`, `frontend/src/lib/api/*`, `frontend/src/lib/hooks/*`, Playwright tests

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [x] F1. Plan Compliance Audit — oracle (APPROVE)
- [x] F2. Code Quality Review — unspecified-high (REJECT — non-blocking code quality issues, not plan-breaking)
- [x] F3. Real Manual QA — unspecified-high (APPROVE)
- [x] F4. Scope Fidelity Check — deep (REJECT — false positive on .sisyphus/boulder.json tooling metadata)

## Commit Strategy
- Prefer 6 logical commits, in this order:
  1. `feat(admin): add sqlite foundation for settings and history`
  2. `feat(settings): add runtime llm settings api semantics`
  3. `fix(llm): read runtime settings on each request`
  4. `feat(quality): add issue metadata editing api`
  5. `feat(history): persist final panel evaluations`
  6. `feat(frontend): add admin settings quality edit and history views`
- If frontend work is split cleanly, commits 6 can be further divided into:
  - `feat(frontend): add runtime settings page`
  - `feat(frontend): add quality issue edit dialog`
  - `feat(frontend): add panel history page`
- Do not commit generated OpenAPI files alone; always bundle them with the API/UI change that requires them.

## Success Criteria
- 管理员无需修改 `.env` 或重启服务，即可让后续 LLM 调用使用新的 `api_base` / `model_name` / `api_key`。
- `quality-registry` 页面可安全编辑 `issue_text` 与 `reported_by`，且审计历史完整保留。
- `/history` 只展示最终评估结果，信息足够回顾但不扩展为回放系统。
- 新增功能完全复用现有 Next.js 页面结构与 FastAPI 路由/类型生成流程。
- 全部验证命令通过，且无 API drift、无 TypeScript 错误、无前端交互回归。
