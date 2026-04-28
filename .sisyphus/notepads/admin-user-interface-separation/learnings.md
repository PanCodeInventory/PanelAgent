# Learnings — admin-user-interface-separation

## 2026-04-22 Plan Generation Phase
- Phase 1 (admin-interface-management) is COMPLETE: all 13 tasks done, settings/history/quality-edit features exist in current codebase
- Backend already has: admin_database.py, llm_settings_store.py, panel_history_store.py, settings.py, panel_history.py endpoints
- Frontend already has: /settings page, /history page, quality edit dialog, all with hooks and API wrappers
- Current frontend uses route-handler proxy (frontend/src/app/api/v1/[...path]/route.ts) + next.config.ts rewrites (dual proxy — must resolve)
- Frontend must use --webpack flag for dev (turbopack fails with @tailwindcss/postcss)
- Frontend AGENTS.md warns: "This is NOT the Next.js you know" — breaking changes in Next.js 16
- Session cookie name locked: panelagent_admin_session
- No basePath — use reverse-proxy prefix stripping instead
- Admin default landing after login: /admin/settings
- History admin namespace: /api/v1/admin/panel-history/* (matching current router prefix /panel-history)
- Route ownership freeze captured in `docs/route-ownership-matrix.md`; later tasks should treat it as the URL contract source of truth.
- Public quality registry is limited to submission endpoints (`POST /issues`, `POST /candidates/lookup`, `POST /candidates/confirm`); list/detail/history/review flows migrate to `/api/v1/admin/quality-registry/*`.
- Legacy browser redirects are page-only: `/settings -> /admin/settings`, `/history -> /admin/history`, and `/admin -> /admin/settings`, all starting as 302.

## 2026-04-22 T2: Admin Router, Session Auth & Auth Endpoints
- Starlette SessionMiddleware requires `itsdangerous` package (not installed by default with starlette 1.0.0; added to backend/requirements.txt)
- SessionMiddleware supports `path` param — set to `/api/v1/admin` so cookie only sent to admin routes
- `https_only` param controls Secure flag; toggled via `ENVIRONMENT=production` env var
- Session cookie max_age set to 28800 (8h) via SessionMiddleware `max_age` param
- Architecture: admin_router has NO router-level dependencies; auth guard applied per-endpoint via `Depends(require_admin_session)`. Login and session-check are exempt; logout uses the dependency.
- `require_admin_session` checks both `is_admin == True` and TTL expiry (clears session on expiry)
- Login uses `hmac.compare_digest` for timing-safe password comparison against `ADMIN_PASSWORD` env var
- Session data is minimal: `{"is_admin": True, "login_at": <float timestamp>}` — no password or API keys
- pytest-asyncio strict mode requires `@pytest.mark.asyncio` on every async test method and `@pytest_asyncio.fixture` for async fixtures
- All 12 new admin auth tests pass; full suite (79 tests) passes with no regressions

## 2026-04-22 T3: Create Independent Admin Frontend App
- Created `admin-frontend/` directory with complete Next.js 16 app structure
- Copied Next.js 16.2.1 and React 19.2.4 versions from frontend/package.json for consistency
- Admin layout has distinct visual identity: dark sidebar with Shield icon, ADMIN badge, different navigation
- Layout uses sidebar nav (控制台, 系统设置, 方案历史, 质量管理) vs frontend's top nav
- Login page is standalone (outside the admin layout) for unauthenticated access
- No basePath in next.config.ts — reverse-proxy handles /admin prefix stripping
- Route structure: / (redirects to /settings), /login, /settings, /history, /quality-registry
- npm install succeeds with 628 packages
- Same Tailwind CSS 4 + shadcn/ui setup as frontend (postcss.config.mjs with @tailwindcss/postcss)
- Copied shadcn components: Button, Card, Input, Label + utils.ts (cn helper)
- Dev server starts on port 3001 independently: `npm run dev -- --port 3001`
- Environment: BACKEND_INTERNAL_URL=http://127.0.0.1:8000 for API proxy (route handlers in future task)

## 2026-04-22 T4: Split quality-registry public/admin backend routes
- Public `backend/app/api/v1/endpoints/quality_registry.py` now only exposes submit-time routes: `POST /issues`, `POST /candidates/lookup`, `POST /candidates/confirm`.
- Protected management routes moved to `backend/app/api/v1/admin/endpoints/quality_registry.py` under `/api/v1/admin/quality-registry/*` with router-level `Depends(require_admin_session)`.
- Keeping separate `QualityRegistryStore()` instances for public/admin modules is safe because the store is file-backed and reloads state from disk on each operation.
- API tests now patch both public and admin quality-registry modules to the same temp store/projector so cross-surface create/list/update/review flows stay deterministic.
- Full pytest after the split leaves four unrelated pre-existing failures in quality-context header tests (`tests/test_panel_evaluate_quality.py`, `tests/test_panel_recommend_quality.py`, `tests/test_quality_context_formatter.py`, `tests/test_quality_e2e_integration.py`), all expecting English header text while current formatter emits Chinese header text.

## 2026-04-23 T11: Dual frontend verification + OpenAPI regression workflow
- `settings` and `panel-history` routers must be mounted only under `admin_router` to keep the OpenAPI contract aligned with `docs/route-ownership-matrix.md` and avoid regenerating stale public client paths.
- Reusing the existing endpoint routers inside `backend/app/api/v1/admin/router.py` with `dependencies=[Depends(require_admin_session)]` migrates them to `/api/v1/admin/*` without touching endpoint business logic.
- Backend regression coverage now explicitly checks unauthenticated `401` responses for `/api/v1/admin/settings/llm` and `/api/v1/admin/panel-history*`, then reuses admin login cookies for happy-path assertions.
- `make generate-client` only regenerates the user frontend's committed OpenAPI types today; `admin-frontend` does not consume a generated client yet, so no Makefile copy step was required.
- Full verification on 2026-04-23 succeeded for OpenAPI generation/drift, both frontend typechecks, and both frontend production builds; backend pytest remained at the expected 4 pre-existing quality-context failures only.

## 2026-04-23 F4: Scope Fidelity Review
- The user frontend still contains admin endpoint strings in `frontend/src/lib/api/generated/index.ts`; even if they are generated types rather than live calls, the plan's guardrail check (`grep /api/v1/admin frontend/src`) fails until admin routes are excluded from the user frontend client surface.
- Project-level monorepo/tooling rewrite did not occur: `frontend/package.json` and `admin-frontend/package.json` contain no workspace/turbo/lerna config, and no root `turbo.json` exists.
- Session storage remains minimal in current backend state: only `is_admin` and `login_at` are written into `request.session`.

## 2026-04-23 F1 Fix: Admin Path Handling
- Created `admin-frontend/src/lib/admin-path.ts` — path helper using `NEXT_PUBLIC_ADMIN_PATH_PREFIX` env var
- Admin nav links were duplicated (old bare + new adminPath) — removed duplicates
- Quality-registry slug was `quality_registry` (underscore) in adminPath but actual route is `quality-registry` (hyphen) — fixed
- Cookie path changed from `/api/v1/admin` to `/` in backend SessionMiddleware — allows admin middleware to read cookie on page routes
- Added `ARG NEXT_PUBLIC_ADMIN_PATH_PREFIX` to `Dockerfile.frontend` (shared Dockerfile)
- Added `build.args.NEXT_PUBLIC_ADMIN_PATH_PREFIX: "/admin"` to `docker-compose.yml` admin-frontend service
- Middleware duplicates adminPath logic inline rather than importing — intentional for Edge runtime compatibility
- Direct access (port 3001): prefix empty, all paths work as root-relative
- Gateway access (port 8080): prefix `/admin`, browser calls `/admin/api/v1/*` and nav links point to `/admin/*`
