# PanelAgent 用户端 / 管理端双前端分离计划

## TL;DR
> **Summary**: 在保留单一 FastAPI 后端的前提下，将当前单 Next.js 前端拆分为两个同仓独立 Next.js 应用：用户端保留在根路径，管理端新增为独立应用并通过同域 `/admin` 前缀对外暴露，同时将管理能力迁移到显式 `/api/v1/admin/*` API 命名空间，并加入单一密码 + session cookie 认证。
> **Deliverables**:
> - 独立的用户端 Next.js 应用与独立的管理端 Next.js 应用
> - 管理端登录 / 登出 / 会话校验与受保护的 `/api/v1/admin/*` 后端边界
> - `/settings` 与 `/history` 完整迁移到管理端
> - `quality-registry` 拆分为用户提交面与管理员审核/编辑面
> - 旧地址重定向、双前端本地/Compose 拓扑、双端测试与文档更新
> **Effort**: XL
> **Parallel**: YES - 3 waves
> **Critical Path**: T1 → T2 → T3 → T5 → T6/T7/T8 → T9 → T10 → T11

## Context
### Original Request
- 用户希望前后端分开两个界面：一个给普通用户，一个给管理员。

### Interview Summary
- 采用**同仓双前端**，不是单前端内简单分组。
- 用户端与管理端使用**同域不同前缀**。
- 管理端采用**单一密码登录**。
- 管理端登录态采用**session cookie**。
- `/settings` 与 `/history` 归管理端。
- `quality-registry` 拆成“用户提交问题”与“管理员审核/编辑/解决”两套界面。
- 旧地址采用 **301/302 重定向** 迁移。

### Repo Findings
- 当前仓库只有一个 Next.js 应用，所有页面共用 `frontend/src/app/layout.tsx:32-109` 的统一导航。
- 当前前端通过 `frontend/src/app/api/v1/[...path]/route.ts:39-75` 与 `frontend/next.config.ts:21-28` 共享一个 API 代理面。
- 当前后端只有一个 FastAPI 应用，`backend/app/main.py:36-44` + `backend/app/api/v1/router.py` 将用户与管理 API 平铺在 `/api/v1` 下。
- 敏感设置写接口 `backend/app/api/v1/endpoints/settings.py:36-80` 当前无鉴权。
- `backend/app/api/v1/endpoints/quality_registry.py:122-330` 当前混合了用户提交与管理员审核流。
- `frontend/playwright.config.ts:10-19`、`docker-compose.yml:36-54`、`Makefile:13-32` 当前都默认只有一个前端表面。

### Metis Review (gaps addressed)
- 已锁定 URL 归属：用户端根路径 `/`；管理端同域 `/admin` 前缀；管理端 API 走显式 `/api/v1/admin/*`。
- 已锁定边界：`/settings`、`/history` 迁移到管理端；`quality-registry` 必须 API 与 UI 双层拆分，不能仅隐藏按钮。
- 已锁定代理策略：保留 route-handler 代理，移除当前与其重复的 rewrite 代理策略，避免双代理歧义。
- 已锁定认证策略：单一密码 + 后端 session cookie + 统一 admin router 依赖保护。
- 已锁定迁移策略：先临时 302，稳定后再切换 301；API 不做浏览器式重定向。
- 已锁定基础结构：不新增第二个后端服务，不做 OAuth/SSO/角色系统，不引入 repo 级 monorepo/tooling 重写。

### Oracle Review (architecture pitfalls addressed)
- 管理端浏览器可见 API 路径必须是 `/admin/api/v1/*`，再由代理转发到后端 `/api/v1/admin/*`，否则 session cookie 的路径与隔离边界会混乱。
- 管理端不能继续复用当前根相对 `fetch("/api/v1/...")` 风格，必须使用**管理端专属 API helper**，默认走 `/admin/api/v1/*`。
- 采用 SessionMiddleware 时必须只存最小认证态，不存密码、密钥或其他敏感信息；密码变更失效策略要明确。

## Work Objectives
### Core Objective
把当前混合式 PanelAgent 前端重构为“用户端 / 管理端”双前端结构，在不拆分后端服务的前提下，建立清晰的用户/管理员 URL、API、登录态、测试和部署边界，使执行代理无需再判断任何页面、端点或代理归属。

### Deliverables
- 保留现有 `frontend/` 作为用户端应用
- 新增独立管理端应用目录：`admin-frontend/`
- 后端新增 admin API 命名空间与 admin 会话接口
- 用户端专属布局、导航、质量提交页面
- 管理端专属布局、登录页、设置页、历史页、质量管理页
- 旧浏览器地址迁移与重定向表
- 双前端 dev / compose / docs / Playwright 方案

### Definition of Done (verifiable conditions with commands)
- `PYTHONPATH=. python -m pytest tests/api/ -q` 通过，且 admin auth、admin namespace、quality split 新增测试全部通过。
- `cd frontend && npx tsc --noEmit` 通过。
- `cd admin-frontend && npx tsc --noEmit` 通过。
- `npm run lint --prefix frontend` 与 `npm run lint --prefix admin-frontend` 通过。
- `make generate-client` 与 `make check-drift` 通过，且双前端消费的 OpenAPI 契约无漂移。
- `cd frontend && npx playwright test` 通过，覆盖用户端关键路径。
- `cd admin-frontend && npx playwright test` 通过，覆盖登录、设置、历史、质量管理关键路径。
- 浏览器访问旧地址 `/settings`、`/history` 时按计划重定向到 `/admin/...`。
- 未登录访问 `/admin/*` 与 `/api/v1/admin/*` 返回预期重定向/401。

### Must Have
- 用户端与管理端必须是两个**独立 Next.js 应用**，不是单 app 下 route group 假分离。
- 用户端继续对外承载 `/`、`/exp-design`、`/panel-design`、`/quality-registry`（仅提交面）。
- 管理端对外承载 `/admin/login`、`/admin/settings`、`/admin/history`、`/admin/quality-registry`。
- 后端管理 API 必须统一挂到 `/api/v1/admin/*`。
- 管理端浏览器侧 API 路径必须统一为 `/admin/api/v1/*`，再代理到后端 `/api/v1/admin/*`。
- 用户端必须去掉设置、历史、管理员审核入口的导航暴露。
- `quality-registry` 必须拆成：
  - 用户端：问题提交、候选匹配确认（如保留）
  - 管理端：列表、详情、审计历史、编辑、审核队列、解决操作
- 管理员认证必须具备：登录、登出、会话检查、TTL、密码来源 env、cookie 安全属性。
- 旧页面路由必须定义明确迁移行为（302→301 演进策略）。

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- 不新增第二个 FastAPI 后端服务。
- 不引入 OAuth、SSO、用户系统、RBAC、角色表。
- 不继续保留当前 rewrite + route-handler 双代理并存的歧义结构。
- 不让用户端继续直接调用 `/api/v1/admin/*`。
- 不通过“隐藏按钮”替代真正的 API 权限边界。
- 不在 SessionMiddleware 中存储密码、API key、完整用户资料。
- 不做 Turborepo / workspace / shared package 大改，除非计划内某任务明确要求且可验证。

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: **hybrid verification**（架构迁移前后都要跑 smoke），不是纯 tests-after
- QA policy: 每个任务必须同时覆盖 happy path 与 failure/unauthenticated path
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Shared dependencies are extracted into Wave 1.

Wave 1: T1-T5 — backend boundary + auth + app scaffolding foundations
- T1 路由与归属矩阵、重定向矩阵、契约冻结
- T2 后端 admin router 与 session auth 基础设施
- T3 quality-registry API 双层拆分
- T4 管理端 Next.js 应用脚手架与 `/admin` 基础路径
- T5 双前端 API 代理与 client 基础设施统一

Wave 2: T6-T9 — page migration and UX split
- T6 用户端 shell 与导航清理
- T7 管理端登录与会话门禁
- T8 设置页与历史页迁移到管理端
- T9 quality-registry 双界面拆分

Wave 3: T10-T11 — infra, tests, docs
- T10 双前端 dev / compose / gateway / docs 更新
- T11 双端 Playwright、lint、typecheck、OpenAPI 工作流完成

### Dependency Matrix (full, all tasks)
| Task | Depends On | Blocks |
|---|---|---|
| T1 | none | T2, T3, T4, T6, T8, T9, T10, T11 |
| T2 | T1 | T3, T5, T7, T8, T9, T11 |
| T3 | T1, T2 | T5, T9, T11 |
| T4 | T1 | T5, T7, T8, T9, T10, T11 |
| T5 | T2, T3, T4 | T6, T7, T8, T9, T11 |
| T6 | T4, T5 | T10, T11 |
| T7 | T2, T4, T5 | T8, T9, T11 |
| T8 | T2, T4, T5, T7 | T10, T11 |
| T9 | T3, T4, T5, T7 | T10, T11 |
| T10 | T4, T6, T8, T9 | T11 |
| T11 | T2, T3, T5, T6, T7, T8, T9, T10 | F1-F4 |

### Agent Dispatch Summary (wave → task count → categories)
| Wave | Task Count | Categories |
|---|---:|---|
| Wave 1 | 5 | deep ×2, unspecified-high ×2, visual-engineering ×1 |
| Wave 2 | 4 | visual-engineering ×3, unspecified-high ×1 |
| Wave 3 | 2 | unspecified-high ×1, deep ×1 |
| Final | 4 | oracle / unspecified-high / deep |

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [x] 1. 冻结路由归属矩阵、API 归属矩阵与旧地址迁移表

  **What to do**:
  - 在实现开始前先产出一份仓库内可执行的“归属矩阵”文档/常量表，明确以下对象的最终归属：
    - 浏览器页面：`/`、`/exp-design`、`/panel-design`、`/quality-registry`、`/settings`、`/history`、`/admin/*`
    - 后端端点：public `/api/v1/*` 与 admin `/api/v1/admin/*`
    - 旧地址：`/settings -> /admin/settings`、`/history -> /admin/history`
  - 明确 `/quality-registry` 在迁移后仍保留为用户端“提交面”，不做浏览器重定向。
  - 生成一份固定迁移表，执行代理后续不得自行改动 URL 决策。

  **Must NOT do**:
  - 不留“待决定的 URL”。
  - 不把 API 重定向与浏览器页面重定向混为一谈。
  - 不继续保留“同一页面同时服务用户与管理员”的模糊定义。

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: 这是整个迁移的契约冻结任务，后续所有实现都依赖它。
  - Skills: []
  - Omitted: [`frontend-design`] - 不是视觉设计任务。

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T2, T3, T4, T6, T8, T9, T10, T11 | Blocked By: none

  **References**:
  - Pattern: `frontend/src/app/layout.tsx:32-109` - 当前所有页面入口混在同一导航里，必须先冻结新归属。
  - Pattern: `backend/app/api/v1/router.py` - 当前后端所有 router 平铺在一个 `/api/v1` 面下。
  - Pattern: `.sisyphus/drafts/admin-user-interface-separation.md` - 已确认的用户偏好与边界。

  **Acceptance Criteria**:
  - [ ] 所有当前页面和 API 都有唯一归属：`user` / `admin` / `shared infra` / `redirected`。
  - [ ] `/settings` 与 `/history` 的旧地址迁移行为被明确写成临时 302 + 稳定后 301 策略。
  - [ ] `/quality-registry` 被明确保留为用户端页面，管理员管理面改为 `/admin/quality-registry`。

  **QA Scenarios**:
  ```
  Scenario: Route ownership matrix is internally consistent
    Tool: Bash
    Steps: run a project-local verification script or grep-based check that every current page path appears exactly once in the route ownership artifact
    Expected: no duplicated ownership entries; `/settings` and `/history` map to admin redirects only; `/quality-registry` remains user-facing
    Evidence: .sisyphus/evidence/task-1-route-ownership.txt

  Scenario: Redirect table excludes API endpoints
    Tool: Bash
    Steps: inspect redirect artifact or route tests to ensure `/api/v1/*` and `/api/v1/admin/*` are not part of browser redirect rules
    Expected: only browser routes are redirected; API calls continue to return status codes instead of redirect HTML
    Evidence: .sisyphus/evidence/task-1-redirect-contract.txt
  ```

  **Commit**: YES | Message: `chore(admin): freeze route ownership and redirect contract` | Files: route ownership artifact, redirect config/tests, related docs

- [x] 2. 建立后端 admin router、session 认证与会话接口

  **What to do**:
  - 在现有 FastAPI 应用内新增统一的 admin 路由边界：`/api/v1/admin/*`。
  - 新增 admin auth 接口：
    - `POST /api/v1/admin/auth/login`
    - `POST /api/v1/admin/auth/logout`
    - `GET /api/v1/admin/auth/session`
  - 在 `backend/app/main.py:36-44` 所在应用层加入 `SessionMiddleware`，使用独立 cookie 名称（建议 `panelagent_admin_session`）。
  - 会话只存最小认证态，例如 `is_admin=true` 与时间戳；不得存密码、API key、完整用户信息。
  - 密码来源固定为环境变量（建议 `ADMIN_PASSWORD`），比较必须使用 `hmac.compare_digest`。
  - 为整个 admin router 加统一依赖 `require_admin_session`，而不是分散到单个端点。
  - cookie 规则固定：`HttpOnly`、`SameSite=Lax`、prod 下 `Secure=true`、TTL=8h、登出即清空。

  **Must NOT do**:
  - 不新增用户表、角色表、OAuth、JWT。
  - 不把认证散落在每个 endpoint 内。
  - 不把 admin session cookie 暴露给前端 JS。
  - 不让 `/api/v1/admin/*` 未鉴权时返回 200。

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 认证边界与中间件设计决定全局安全模型。
  - Skills: []
  - Omitted: [`fastapi-templates`] - 不是从零搭 FastAPI 项目。

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T3, T5, T7, T8, T9, T11 | Blocked By: T1

  **References**:
  - Pattern: `backend/app/main.py:36-44` - 当前 app 只挂了 CORS，没有任何 session/auth middleware。
  - Pattern: `backend/app/api/v1/endpoints/settings.py:36-80` - 当前敏感设置写接口无保护。
  - Pattern: `backend/app/api/v1/router.py` - 当前 router 汇总点，适合新增 admin 子边界。
  - External: Oracle architecture consult in session `ses_24b6e5cf1ffe7YxlZLDnLlSx2S` - cookie path and namespace constraints.

  **Acceptance Criteria**:
  - [ ] 未登录访问任意 `/api/v1/admin/*` 返回 401。
  - [ ] 正确密码登录后，`/api/v1/admin/auth/session` 返回 authenticated 状态并携带预期 cookie。
  - [ ] 登出后同一 cookie 再访问 `/api/v1/admin/*` 返回 401。
  - [ ] 密码不正确时不返回 `Set-Cookie`。

  **QA Scenarios**:
  ```
  Scenario: Unauthenticated admin API is blocked
    Tool: Bash
    Steps: curl -i http://127.0.0.1:8000/api/v1/admin/settings/llm
    Expected: HTTP 401; no settings payload returned
    Evidence: .sisyphus/evidence/task-2-admin-auth-unauth.txt

  Scenario: Login creates working admin session and logout clears it
    Tool: Bash
    Steps: curl -i -c /tmp/panelagent-admin.cookies -X POST http://127.0.0.1:8000/api/v1/admin/auth/login -H 'Content-Type: application/json' -d '{"password":"admin-test-password"}' ; curl -i -b /tmp/panelagent-admin.cookies http://127.0.0.1:8000/api/v1/admin/auth/session ; curl -i -b /tmp/panelagent-admin.cookies -X POST http://127.0.0.1:8000/api/v1/admin/auth/logout ; curl -i -b /tmp/panelagent-admin.cookies http://127.0.0.1:8000/api/v1/admin/settings/llm
    Expected: login returns 200/204 with Set-Cookie; session endpoint returns authenticated; post-logout settings request returns 401
    Evidence: .sisyphus/evidence/task-2-admin-auth-session.txt
  ```

  **Commit**: YES | Message: `feat(admin-api): add session auth and admin router namespace` | Files: `backend/app/main.py`, `backend/app/api/v1/router.py`, auth dependency/endpoint files, tests

- [x] 3. 将 quality-registry 后端拆分为 public 提交流与 admin 管理流

  **What to do**:
  - 重新划分 quality-registry 端点：
    - 保留 public：问题创建、候选查找、候选确认（若提交流仍需）
    - 迁移到 admin：问题列表、问题详情、审计历史、编辑、review queue、resolve
  - 管理端所有 quality 管理端点统一改为 `/api/v1/admin/quality-registry/*`。
  - public 端点继续保留在 `/api/v1/quality-registry/*`，但只覆盖“提交问题”最小闭环。
  - 更新 schema、OpenAPI、后端测试，确保 public/admin 端点边界不重叠。

  **Must NOT do**:
  - 不继续让 public `/quality-registry` 暴露列表/编辑/审核能力。
  - 不只改 UI，不改 API。
  - 不破坏现有 issue 审计历史结构。

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: 这是当前最混合的用户/管理员边界，必须 API 级拆分。
  - Skills: []
  - Omitted: [`git-master`] - 非 git 操作。

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T5, T9, T11 | Blocked By: T1, T2

  **References**:
  - Pattern: `backend/app/api/v1/endpoints/quality_registry.py:122-330` - 当前同一 namespace 中混合提交、编辑、审核、解决流。
  - Pattern: `frontend/src/app/quality-registry/quality-registry-client.tsx` - 当前单页混合了用户与管理员视图状态。
  - Pattern: `frontend/src/lib/hooks/use-quality-registry.ts` - 当前 hook 同时暴露 create、update、review 动作。

  **Acceptance Criteria**:
  - [ ] public 端点无法列出所有 issue，也无法编辑或解决 issue。
  - [ ] admin 端点完整支持 list / history / edit / review queue / resolve。
  - [ ] OpenAPI 中 public 与 admin quality 端点路径清晰分离。

  **QA Scenarios**:
  ```
  Scenario: Public quality API only supports submission flow
    Tool: Bash
    Steps: curl -i http://127.0.0.1:8000/api/v1/quality-registry/issues ; curl -i -X PUT http://127.0.0.1:8000/api/v1/quality-registry/issues/test-id -H 'Content-Type: application/json' -d '{"issue_text":"x","reported_by":"y"}'
    Expected: public list/edit calls return 404/405 and are unavailable; submission endpoints remain callable
    Evidence: .sisyphus/evidence/task-3-quality-public-boundary.txt

  Scenario: Admin quality API exposes full management capabilities
    Tool: Bash
    Steps: login as admin, then call `/api/v1/admin/quality-registry/issues`, `/api/v1/admin/quality-registry/issues/{id}/history`, and `/api/v1/admin/quality-registry/review-queue`
    Expected: authenticated responses return 200 with expected management payloads; unauthenticated calls return 401
    Evidence: .sisyphus/evidence/task-3-quality-admin-boundary.txt
  ```

  **Commit**: YES | Message: `refactor(quality): split public and admin quality endpoints` | Files: `backend/app/api/v1/endpoints/quality_registry.py`, schemas, hooks/tests/OpenAPI artifacts

- [x] 4. 新建独立管理端 Next.js 应用并固定 `/admin` 对外前缀

  **What to do**:
  - 在 repo 根目录新增独立应用目录：`admin-frontend/`。
  - 该应用必须是完整独立 Next.js 应用，具备自己的 `package.json`、`src/app`、`tsconfig`、`playwright.config.ts`、`next.config.ts`。
  - 对外 URL 固定为 `/admin` 前缀；实现方式固定为**部署层 path-based routing / prefix stripping**，不使用 Next.js `basePath`，以避免管理端 fetch 路径与 cookie 作用域混乱。
  - 管理端页面最少包括：`/admin/login`、`/admin`、`/admin/settings`、`/admin/history`、`/admin/quality-registry`。
  - 管理端风格可复用现有 shadcn 组件，但必须拥有独立 layout、独立 nav、独立标题与 admin banner。

  **Must NOT do**:
  - 不在现有 `frontend/` 中继续混放管理页。
  - 不依赖单 app route group 来假装“两个独立前端”。
  - 不引入 workspace/monorepo 工具链重写，除非后续任务证明确有阻塞。

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 需要建立独立前端壳层、布局、导航与登录入口。
  - Skills: [`nextjs-app-router-fundamentals`] - 需要稳定处理新 Next.js app 与 App Router 结构。
  - Omitted: [`frontend-design`] - 重点是信息架构隔离，不是品牌重设计。

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: T5, T7, T8, T9, T10, T11 | Blocked By: T1

  **References**:
  - Pattern: `frontend/src/app/layout.tsx:32-109` - 当前共享壳层必须停止承担管理端职责。
  - Pattern: `frontend/package.json:5-12` - 现有 Next app script 结构，可作为 admin app package script baseline。
  - Pattern: `frontend/playwright.config.ts:10-19` - 现有测试配置，需要在 admin app 中建立对应独立配置。

  **Acceptance Criteria**:
  - [ ] `admin-frontend/` 可独立安装、独立启动、独立 typecheck。
  - [ ] 管理端具有独立 layout，不再复用用户端导航。
  - [ ] 管理端首页与登录页在未完成业务迁移前也能独立渲染。

  **QA Scenarios**:
  ```
  Scenario: Admin frontend boots independently
    Tool: Bash
    Steps: npm install --prefix admin-frontend && npm run dev --prefix admin-frontend -- --port 3001
    Expected: admin frontend starts without depending on user frontend runtime
    Evidence: .sisyphus/evidence/task-4-admin-frontend-boot.txt

  Scenario: Admin shell is visually separate from user shell
    Tool: Playwright
    Steps: open user `/`; open admin `/admin/login`; compare presence of admin-only nav links and admin banner/testids
    Expected: user shell shows no admin nav; admin login renders admin shell only
    Evidence: .sisyphus/evidence/task-4-admin-shell.png
  ```

  **Commit**: YES | Message: `feat(admin-frontend): scaffold standalone admin app` | Files: `admin-frontend/**`

- [x] 5. 统一双前端 API 代理与 client 基础设施，消除双代理歧义

  **What to do**:
  - 用户端保留浏览器可见 `/api/v1/*` 调用入口，但统一通过单一路由代理实现，不再同时依赖 `next.config.ts` rewrites 与 route-handler 双通道。
  - 管理端新增**专属 API helper**，浏览器侧固定访问 `/admin/api/v1/*`，再由管理端应用代理到后端 `/api/v1/admin/*`。
  - 所有管理端页面、hooks、server actions（若有）必须改用 admin 专属 helper；不得继续使用根相对 `fetch("/api/v1/...")`。
  - 将 OpenAPI 生成产物或 hand-written client 组织成“双前端各自消费、共享同一后端契约”的结构；若需共享 schema 文件，只共享生成结果，不引入新 workspace。
  - 环境变量命名固定为：两个 Next.js 应用都使用 `BACKEND_INTERNAL_URL` 作为 route-handler 到 FastAPI 的唯一上游地址；浏览器端一律只打同源 `/api/v1/*` 或 `/admin/api/v1/*`，不新增 admin 专属 public backend URL 变量。

  **Must NOT do**:
  - 不保留 rewrite 与 route-handler 并存。
  - 不让 admin app 直接调用 public `/api/v1/*` 来获取管理数据。
  - 不让用户端获得对 `/api/v1/admin/*` 的可达 helper。
  - 不通过 basePath 隐式拼接导致 `fetch` 前缀错乱。

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 涉及 Next.js 代理、环境变量、API client 组织和跨 app 调用边界。
  - Skills: [`nextjs-app-router-patterns`] - 需要稳定处理 App Router 下的代理与 server/client 调用模式。
  - Omitted: [`frontend-design`] - 不是视觉任务。

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T6, T7, T8, T9, T11 | Blocked By: T2, T3, T4

  **References**:
  - Pattern: `frontend/src/app/api/v1/[...path]/route.ts:39-75` - 当前已有 route-handler 代理基础，可作为用户端唯一代理入口。
  - Pattern: `frontend/next.config.ts:21-28` - 当前 rewrite 与 route-handler 重叠，必须移除其一。
  - Pattern: `frontend/src/lib/api/generated/index.ts` - 当前用户端 API client 入口，后续需明确 user/admin 消费边界。
  - External: Oracle architecture consult in session `ses_24b6e5cf1ffe7YxlZLDnLlSx2S` - admin browser path must remain `/admin/api/v1/*` and avoid basePath coupling.

  **Acceptance Criteria**:
  - [ ] 用户端只通过单一代理路径访问 public API，不再存在重复代理配置。
  - [ ] 管理端所有 API 请求默认命中 `/admin/api/v1/*`，最终转发至后端 `/api/v1/admin/*`。
  - [ ] 全仓不存在管理端页面继续使用根相对 public helper 访问 admin 数据的调用点。

  **QA Scenarios**:
  ```
  Scenario: User and admin proxies target different backend namespaces
    Tool: Bash
    Steps: inspect route handlers/config and run app-local smoke requests against `/api/v1/settings/llm` and `/admin/api/v1/auth/session` with backend logs enabled
    Expected: user requests hit public `/api/v1/*`; admin requests hit `/api/v1/admin/*`; no rewrite fallback path remains
    Evidence: .sisyphus/evidence/task-5-proxy-boundary.txt

  Scenario: Admin UI cannot accidentally use user helper paths
    Tool: Bash
    Steps: run a repository search for `"/api/v1/"` under `admin-frontend/` excluding dedicated admin proxy implementation files
    Expected: no stray root-relative public API calls remain in admin app code
    Evidence: .sisyphus/evidence/task-5-admin-helper-audit.txt
  ```

  **Commit**: NO | Message: `refactor(frontend): separate user shell from admin surfaces` | Files: staged together with T6 changes

- [x] 6. 清理用户端壳层与导航，只保留普通用户能力

  **What to do**:
  - 更新 `frontend/` 的根 layout、首页卡片、导航分组与任何快捷入口，移除 `/settings`、`/history`、质量审核/编辑等管理员入口。
  - 用户端保留 `/`、`/exp-design`、`/panel-design`、`/quality-registry`（仅提交面）与必要的帮助文案。
  - 为旧的 `/settings`、`/history` 浏览器入口添加显式重定向到 `/admin/settings`、`/admin/history`；迁移期默认 302，并在配置中预留切换到 301 的明确位置。
  - 若首页/导航当前引用历史页或设置页文案，必须同步改写，避免用户端出现“无权限但可见”的悬空入口。

  **Must NOT do**:
  - 不在用户端保留任何“管理员请前往...”的功能按钮冒充隔离。
  - 不删除用户端质量问题提交能力。
  - 不让浏览器访问旧地址时落入 404，而不是按计划重定向。

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 这是用户端 IA/导航与页面入口的清理任务。
  - Skills: [`nextjs-app-router-fundamentals`] - 需要稳定处理 route-level redirect 与 layout 更新。
  - Omitted: [`shadcn`] - 主要是信息架构调整，不是组件库扩展。

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: T10, T11 | Blocked By: T4, T5

  **References**:
  - Pattern: `frontend/src/app/layout.tsx:32-109` - 当前用户导航仍混有设置、历史入口。
  - Pattern: `frontend/src/app/settings/page.tsx` - 现有设置页实现将迁移到管理端，用户端仅保留重定向职责。
  - Pattern: `frontend/src/app/history/page.tsx` - 现有历史页实现将迁移到管理端，用户端仅保留重定向职责。
  - Pattern: `frontend/src/app/quality-registry/page.tsx` - 用户端质量页面保留，但职责需收缩为提交面。

  **Acceptance Criteria**:
  - [ ] 用户端导航中不再出现设置、历史、质量管理入口。
  - [ ] 访问旧地址 `/settings`、`/history` 会按计划跳转到 `/admin/settings`、`/admin/history`。
  - [ ] 用户端首页与相关说明文本只描述普通用户工作流。

  **QA Scenarios**:
  ```
  Scenario: User shell exposes only user features
    Tool: Playwright
    Steps: open `/`; inspect nav and visible CTA labels; navigate to `/quality-registry`
    Expected: no settings/history/admin review entry is visible; quality page only shows submission-related controls
    Evidence: .sisyphus/evidence/task-6-user-shell.png

  Scenario: Legacy admin pages redirect from user app
    Tool: Playwright
    Steps: open `/settings` then `/history` in a fresh browser context
    Expected: browser lands on `/admin/settings` and `/admin/history` via temporary redirect behavior
    Evidence: .sisyphus/evidence/task-6-legacy-redirects.txt
  ```

  **Commit**: YES | Message: `refactor(frontend): separate user shell from admin surfaces` | Files: `frontend/src/app/layout.tsx`, user route redirects, user copy/nav files, proxy/client files from T5

- [x] 7. 实现管理端登录页、会话门禁与未登录跳转

  **What to do**:
  - 在 `admin-frontend/` 中实现 `/admin/login` 登录页，只接受单一密码输入并调用 `POST /admin/api/v1/auth/login`。
  - 实现管理端会话探测逻辑：应用启动、路由切换或 SSR/route guard 时检查 `/admin/api/v1/auth/session`。
  - 统一门禁方案固定为：`middleware.ts` 先基于 `panelagent_admin_session` cookie 做粗筛重定向；受保护的 admin layout 再通过 `/admin/api/v1/auth/session` 做权威校验，未登录一律跳转 `/admin/login`。
  - 已登录访问 `/admin/login` 时固定跳转到 `/admin/settings`；`/admin` 主页也固定 server-side redirect 到 `/admin/settings`。
  - 实现登出按钮，调用 `/admin/api/v1/auth/logout` 后清理前端缓存并返回登录页。

  **Must NOT do**:
  - 不在前端保存密码到 localStorage/sessionStorage。
  - 不让未登录用户看到管理内容后再 client-side 弹回。
  - 不在多个页面各自手写不同的登录检查逻辑。

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 同时涉及登录交互、路由保护和管理端导航状态。
  - Skills: [`nextjs-app-router-patterns`] - 需要稳定处理 App Router 门禁与重定向。
  - Omitted: [`frontend-design`] - 不是品牌视觉探索。

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: T8, T9, T11 | Blocked By: T2, T4, T5

  **References**:
  - Pattern: `backend/app/main.py` - session middleware/cookie 由后端统一下发，前端只做门禁消费。
  - Pattern: `backend/app/api/v1/router.py` - admin auth/session endpoint namespace 将挂在 `/api/v1/admin/*`。
  - Pattern: `admin-frontend/src/app/layout.tsx` - 管理端统一门禁最适合落在独立 layout 或 middleware。
  - External: Oracle architecture consult in session `ses_24b6e5cf1ffe7YxlZLDnLlSx2S` - cookie path and admin namespace constraints.

  **Acceptance Criteria**:
  - [ ] 未登录访问任意 `/admin/*` 业务页会跳转 `/admin/login`。
  - [ ] 登录成功后默认落到固定管理首页，并能刷新保持会话。
  - [ ] 登出后刷新任意管理页都会重新回到 `/admin/login`。

  **QA Scenarios**:
  ```
  Scenario: Unauthenticated admin page access redirects to login
    Tool: Playwright
    Steps: clear cookies; open `/admin/settings`
    Expected: browser is redirected to `/admin/login`; no protected content flashes on screen
    Evidence: .sisyphus/evidence/task-7-admin-login-gate.txt

  Scenario: Login and logout round-trip works end-to-end
    Tool: Playwright
    Steps: open `/admin/login`; submit wrong password once; submit correct password; verify landing page; click logout; revisit `/admin/history`
    Expected: wrong password shows inline error with no session; correct password grants access; logout returns to login and protected revisit redirects again
    Evidence: .sisyphus/evidence/task-7-admin-login-roundtrip.png
  ```

  **Commit**: NO | Message: `feat(admin-frontend): add login settings and history pages` | Files: staged together with T8 changes

- [x] 8. 将设置页与历史页完整迁移到管理端应用

  **What to do**:
  - 将现有设置页与历史页 UI、hooks、API 调用改造成管理端页面：`/admin/settings`、`/admin/history`。
  - 所有设置相关调用必须改用 admin API helper，命中 `/admin/api/v1/settings/*` → 后端 `/api/v1/admin/settings/*`。
  - 所有历史相关调用必须改用 admin API helper，固定命中 `/admin/api/v1/panel-history/*`，并转发到后端 `/api/v1/admin/panel-history/*`。
  - 保留 Phase 1 已完成的功能能力：LLM provider/model/base URL/API key 修改、历史列表/详情查看。
  - 当前 public `/api/v1/settings/*` 与 `/api/v1/panel-history/*` 在迁移后改为 `/api/v1/admin/settings/*` 与 `/api/v1/admin/panel-history/*`；用户端不再保留对应业务端点消费。

  **Must NOT do**:
  - 不复制出两套长期并存的设置/历史实现。
  - 不让管理端继续依赖用户端 `frontend/src/lib/hooks/*` 直接跨目录 import。
  - 不在迁移后保留 public 可写设置入口。

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 需要把现有页面能力迁移进新 admin app 并接上新 API namespace。
  - Skills: [`nextjs-app-router-fundamentals`] - 需要稳妥迁移页面、hooks、route structure。
  - Omitted: [`shadcn`] - 组件库不是主要风险点。

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: T10, T11 | Blocked By: T2, T4, T5, T7

  **References**:
  - Pattern: `frontend/src/app/settings/settings-client.tsx` - 现有设置 UI，可迁移但需替换 API helper。
  - Pattern: `frontend/src/app/history/history-client.tsx` - 现有历史 UI，可迁移到 admin app。
  - Pattern: `frontend/src/lib/api/settings.ts` - 当前设置 API wrapper，后续需 admin 专属版本。
  - Pattern: `frontend/src/lib/api/panel-history.ts` - 当前历史 API wrapper，后续需 admin 专属版本。
  - Pattern: `frontend/src/lib/hooks/use-settings.ts` - 当前设置 hook 逻辑可复用，但不能跨 app 直接耦合。
  - Pattern: `frontend/src/lib/hooks/use-panel-history.ts` - 当前历史 hook 逻辑可复用，但不能跨 app 直接耦合。

  **Acceptance Criteria**:
  - [ ] `/admin/settings` 可完整读取与更新 LLM 设置，且未登录时不可访问。
  - [ ] `/admin/history` 可查看历史列表与详情，且未登录时不可访问。
  - [ ] 用户端不再渲染原始设置页/历史页业务内容。

  **QA Scenarios**:
  ```
  Scenario: Admin settings page can read and update model configuration
    Tool: Playwright
    Steps: login as admin; open `/admin/settings`; edit provider/model/base URL/API key fields; save; reload page
    Expected: save succeeds; masked API key behavior remains correct; reloaded page reflects persisted settings
    Evidence: .sisyphus/evidence/task-8-admin-settings.png

  Scenario: Admin history page shows persisted panel evaluations only after auth
    Tool: Playwright
    Steps: login as admin; open `/admin/history`; open one history detail; then clear cookies and revisit the same URL
    Expected: authenticated session sees list/detail; cleared session is redirected to `/admin/login`
    Evidence: .sisyphus/evidence/task-8-admin-history.txt
  ```

  **Commit**: YES | Message: `feat(admin-frontend): add login settings and history pages` | Files: `admin-frontend/src/app/settings/**`, `admin-frontend/src/app/history/**`, admin hooks/api wrappers, related backend namespace adjustments

- [x] 9. 将 quality-registry 拆成用户提交界面与管理员管理界面

  **What to do**:
  - 用户端 `/quality-registry` 仅保留提交闭环：填写问题、候选匹配确认、成功提示，以及与提交直接相关的最小查询能力。
  - 管理端 `/admin/quality-registry` 提供完整管理面：列表筛选、详情、审计历史、编辑、审核队列、resolve 操作。
  - 将当前混合 hook/component 拆成 user/admin 两套，避免一个 hook 暴露 create/update/review 全能力。
  - 若当前用户端 UI 中存在编辑按钮、审核状态、解决按钮、全量列表表格，必须全部迁移到管理端。
  - 明确管理端默认排序、筛选和空状态文案；建议管理端首页卡片展示待审核数量，便于登录后直达处理。

  **Must NOT do**:
  - 不保留“同一组件通过 isAdmin 切换行为”的长期结构。
  - 不让用户端继续看到其他人提交的问题列表。
  - 不让管理端缺失审计历史或 resolve 路径，导致只拆半套。

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 这是最复杂的前端职责拆分，牵涉表单、表格、详情、审核动作。
  - Skills: [`nextjs-app-router-patterns`] - 需要稳定处理多页面数据流和受保护路由。
  - Omitted: [`frontend-design`] - 重点是职责拆分而非重新设计品牌视觉。

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: T10, T11 | Blocked By: T3, T4, T5, T7

  **References**:
  - Pattern: `frontend/src/app/quality-registry/quality-registry-client.tsx` - 当前单页混合用户提交与管理员管理行为。
  - Pattern: `frontend/src/lib/hooks/use-quality-registry.ts` - 当前 hook 混合 create、update、review 动作。
  - Pattern: `frontend/src/lib/api/quality-registry.ts` - 当前 API wrapper 需拆为 user/admin 两个边界。
  - Pattern: `backend/app/api/v1/endpoints/quality_registry.py` - 后端端点在 T3 后将提供清晰的 public/admin namespace。

  **Acceptance Criteria**:
  - [ ] 用户端 `/quality-registry` 只能完成提交流程，不显示管理列表/编辑/解决能力。
  - [ ] 管理端 `/admin/quality-registry` 完整提供列表、详情、历史、编辑、审核、解决能力。
  - [ ] user/admin 两端的 hooks 与 API wrappers 已物理分离，职责边界清晰。

  **QA Scenarios**:
  ```
  Scenario: User quality page only supports submission workflow
    Tool: Playwright
    Steps: open `/quality-registry`; submit a new issue; inspect visible controls and table regions
    Expected: submission succeeds; no admin-only review/edit/resolve controls are rendered
    Evidence: .sisyphus/evidence/task-9-quality-user.png

  Scenario: Admin quality page supports full moderation workflow
    Tool: Playwright
    Steps: login as admin; open `/admin/quality-registry`; open an issue detail; edit fields; inspect audit history; resolve the issue
    Expected: list/detail/history/edit/resolve all work under auth; resolving updates list status and audit trail
    Evidence: .sisyphus/evidence/task-9-quality-admin.png
  ```

  **Commit**: YES | Message: `feat(quality): split user submission and admin management ui` | Files: `frontend/src/app/quality-registry/**`, `admin-frontend/src/app/quality-registry/**`, split hooks/api wrappers, related tests

- [x] 10. 更新双前端本地开发、Compose、网关与文档拓扑

  **What to do**:
  - 扩展本地开发命令，使用户端、管理端、后端都能被明确启动；端口固定为 user frontend `3000`、admin frontend `3001`、backend `8000`；补齐 `Makefile` 或等价脚本中的双前端入口。
  - 更新 `docker-compose.yml`，使 compose 环境包含 user frontend、admin frontend、backend，并明确端口/服务名/依赖顺序；集成网关宿主端口固定为 `8080` 用于同域 `/` + `/admin` 联调。
  - 新增或更新反向代理配置，固定路由规则为：`/admin/api/v1/*` 与 `/admin/*`（含 `/_next` 资源）转发到 admin app 并剥离 `/admin` 前缀；`/api/v1/*` 与非 admin 页面转发到 user app；FastAPI 继续暴露内部 `8000` 供 direct API smoke 使用。
  - 更新 `README.md` 与相关文档，明确环境变量、端口、启动方式、路由归属和认证说明。
  - 为 302→301 重定向演进策略在文档中留出操作说明，避免部署后行为不一致。

  **Must NOT do**:
  - 不只更新代码，不更新启动文档。
  - 不让 compose/dev 命令默认仍只启动一个前端。
  - 不在文档里留下与实际端口、路径不一致的示例。

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 需要统一本地/容器/文档的运行拓扑。
  - Skills: [`readme`] - 需要将运行与架构说明同步到文档。
  - Omitted: [`git-master`] - 非 git 工作。

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: T11 | Blocked By: T4, T6, T8, T9

  **References**:
  - Pattern: `docker-compose.yml:36-54` - 当前 compose 假设只有一个前端服务。
  - Pattern: `Makefile:13-32` - 当前本地命令只覆盖单前端。
  - Pattern: `README.md` - 当前运行说明仍只描述 `frontend/`。
  - Pattern: `frontend/playwright.config.ts` - 当前 webServer 启动假设需要在双前端文档/命令中同步调整。

  **Acceptance Criteria**:
  - [ ] 本地开发文档能明确启动 user frontend、admin frontend、backend 三者。
  - [ ] Compose 环境中可同时访问用户端和管理端。
  - [ ] README 中的端口、路径、环境变量与实际实现一致。

  **QA Scenarios**:
  ```
  Scenario: Dual-frontend compose stack boots with expected routes
    Tool: Bash
    Steps: docker compose up --build -d; call user root, admin login, and backend health/OpenAPI endpoints
    Expected: `/` serves user app, `/admin/login` serves admin app, backend API remains reachable
    Evidence: .sisyphus/evidence/task-10-compose-smoke.txt

  Scenario: Developer docs match actual commands
    Tool: Bash
    Steps: follow README commands verbatim in a clean shell for backend, user frontend, and admin frontend startup
    Expected: all documented commands run successfully without undocumented extra flags
    Evidence: .sisyphus/evidence/task-10-readme-smoke.txt
  ```

  **Commit**: NO | Message: `chore(infra): update dual-frontend tests docker and docs` | Files: staged together with T11 changes

- [x] 11. 完成双前端测试、类型检查、OpenAPI 契约与回归工作流

  **What to do**:
  - 为用户端与管理端分别建立/更新 Playwright 配置、测试夹具与基础 smoke flows。
  - 补齐后端 pytest 覆盖：admin auth、admin namespace、public/admin quality boundary、settings/history admin-only 访问控制。
  - 确保 `make generate-client` 与 `make check-drift` 覆盖到双前端消费场景；若 admin app 也消费生成客户端，必须把生成/复制流程写进统一命令。
  - 为 `frontend/` 与 `admin-frontend/` 分别接入 `tsc --noEmit`、lint、必要的 build smoke。
  - 整理一条可重复执行的总验证顺序，供最终 F1-F4 验证波复用。

  **Must NOT do**:
  - 不只测试 happy path，不测未登录与越权路径。
  - 不让 admin app 依赖手工复制生成物却没有自动化命令。
  - 不把用户端与管理端的 E2E 混进一套难以维护的单配置里，除非有明确的项目级夹具共享策略。

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: 需要整合后端权限测试、双前端 E2E、OpenAPI 生成和全仓质量门。
  - Skills: []
  - Omitted: [`playwright`] - 计划中定义 Playwright 使用方式即可，实际执行时再调用。

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: F1, F2, F3, F4 | Blocked By: T2, T3, T5, T6, T7, T8, T9, T10

  **References**:
  - Pattern: `frontend/playwright.config.ts:10-19` - 现有 E2E 结构，可复制出 admin 侧独立配置。
  - Pattern: `tests/api/test_settings.py` - 当前 settings API 测试，可迁移为 admin-only 断言。
  - Pattern: `tests/api/test_panel_history.py` - 当前 history API 测试，可迁移为 admin-only 断言。
  - Pattern: `tests/api/test_quality_registry_update.py` - 当前 quality 编辑测试，可扩展为 public/admin 边界测试。
  - Pattern: `Makefile` - 统一入口应在这里汇总 typecheck/lint/OpenAPI/test 命令。

  **Acceptance Criteria**:
  - [ ] 后端 pytest 覆盖 admin auth、admin-only settings/history、quality public/admin split，并全部通过。
  - [ ] `frontend/` 与 `admin-frontend/` 的 lint、typecheck、Playwright smoke 全部通过。
  - [ ] OpenAPI 生成与 drift 检查在双前端消费场景下无漂移。
  - [ ] 最终验证命令序列被写入文档或 Make target，可供 F1-F4 直接复用。

  **QA Scenarios**:
  ```
  Scenario: Repository-wide verification sequence passes
    Tool: Bash
    Steps: run backend pytest, both frontend lint/typecheck commands, OpenAPI generate/check-drift, then both Playwright suites in documented order
    Expected: every command exits 0; no generated client drift remains; artifacts are captured for both apps
    Evidence: .sisyphus/evidence/task-11-full-verification.txt

  Scenario: Unauthorized paths are covered by automated tests
    Tool: Bash
    Steps: inspect and execute targeted tests for unauthenticated `/api/v1/admin/*`, `/admin/*`, and public `/quality-registry` restrictions
    Expected: failing access paths are explicitly asserted in pytest/Playwright rather than only manual smoke-tested
    Evidence: .sisyphus/evidence/task-11-auth-boundary.txt
  ```

  **Commit**: YES | Message: `chore(infra): update dual-frontend tests docker and docs` | Files: `frontend/playwright.config.ts`, `admin-frontend/playwright.config.ts`, `tests/api/**`, `Makefile`, `README.md`, `docker-compose.yml`, generated client workflow files

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [x] F1. Plan Compliance Audit — oracle
- [x] F2. Code Quality Review — unspecified-high
- [x] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [x] F4. Scope Fidelity Check — deep

## Commit Strategy
- Prefer 8 logical commits, in this order:
  1. `chore(admin): freeze route ownership and redirect contract`
  2. `feat(admin-api): add session auth and admin router namespace`
  3. `refactor(quality): split public and admin quality endpoints`
  4. `feat(admin-frontend): scaffold standalone admin app`
  5. `refactor(frontend): separate user shell from admin surfaces`
  6. `feat(admin-frontend): add login settings and history pages`
  7. `feat(quality): split user submission and admin management ui`
  8. `chore(infra): update dual-frontend tests docker and docs`

## Success Criteria
- 用户端访问 `/` 系列页面时不再看到管理入口，也不会调用 admin API。
- 管理员未登录访问 `/admin/*` 会被重定向到 `/admin/login`，未登录调用 `/api/v1/admin/*` 返回 401。
- 管理员登录后可在 `/admin/settings` 管理 LLM 配置，在 `/admin/history` 查看历史，在 `/admin/quality-registry` 审核与编辑质量条目。
- `/quality-registry` 在用户端只保留提交相关能力，不再暴露管理操作。
- 旧页面地址按既定策略迁移，不出现悬空入口。
- 双前端本地开发、Compose、Playwright、OpenAPI、lint/typecheck 全部可重复执行。
