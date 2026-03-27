
- 2026-03-27 scope fidelity check rejected `ea57edd..HEAD`: unplanned dependency additions landed in `frontend/package.json` (for example `@base-ui/react`, `lucide-react`, `recharts`, `class-variance-authority`, `clsx`, `tailwind-merge`, `tw-animate-css`) without being named in the plan, and Task 10 CI in `.github/workflows/ci.yml` omits required `mypy` and frontend e2e gates.
- 2026-03-27 scope fidelity check also found task/file drift: `scripts/generate-openapi.py`, `Makefile`, and `PARITY_GATE.md` were added outside the plan's commit file lists, while Tasks 8-9 landed without the planned `frontend/tests/e2e/**` coverage artifacts.

- 2026-03-27 code quality review rejected current migration slice: backend wrappers return transport-level 200 for operational failures (`backend/app/api/v1/endpoints/panels.py`, `backend/app/api/v1/endpoints/recommendations.py`, `backend/app/api/v1/endpoints/spectra.py`), which hides real failures from clients, caches, and monitoring.
- 2026-03-27 security review found arbitrary file path ingestion via `inventory_file` in `backend/app/api/v1/endpoints/panels.py` and `backend/app/api/v1/endpoints/recommendations.py`; absolute paths and repo-relative paths are accepted without confinement to the inventory directory.
- 2026-03-27 frontend review found hooks do not consistently honor backend `status == "error"`: `frontend/src/lib/hooks/use-marker-recommendation.ts` and `frontend/src/lib/hooks/use-panel-evaluation.ts` can treat error payloads as successful responses, dropping server messages and leaving UI in misleading states.
- 2026-03-27 type/quality review found the panel evaluation contract is weakly typed end-to-end (`backend/app/schemas/panels.py` uses `Any`; `frontend/src/lib/hooks/use-panel-evaluation.ts` relies on casts), reducing generated-client value and masking schema drift.
- 2026-03-27 test review found no frontend automated coverage for pages/hooks and no API tests for malformed input / validation / path-restriction behavior, leaving migration regressions under-protected despite backend happy-path tests passing.

## 2026-03-27 Plan Compliance Audit
- Rejected plan compliance: Tasks 1, 3, 4, 5, 8, 9, and 10 have gaps between the checked plan state and the implemented artifacts.
- Task 1 lacks any multi-encoding fixture/test coverage even though the plan requires it.
- Tasks 3-5 have plan commit file paths that do not exist in the repo; endpoints were implemented under backend/app/api/v1/endpoints instead.
- Task 5 also does not provide tests/api/test_evaluation_fallbacks.py as named in the acceptance criteria.
- Tasks 8-9 lack Playwright/e2e coverage and the planned component directories/frontend test paths do not exist.
- Task 9 hardcodes Human_Inventory.csv in frontend hooks, which does not match streamlit_app.py INVENTORY_CONFIG (inventory/Human_20250625_ZhengLab.csv).
- Task 10 quality gates are incomplete: CI has no frontend e2e job, no backend typecheck gate, and backend lint is explicitly non-blocking.

- F4 rerun (2026-03-27): REJECT. Explicit plan gates for `npm run test:e2e --prefix frontend` remain unmet: `frontend/package.json` has no `test:e2e` script, no Playwright dependency, and `frontend/tests/e2e/**` is absent. CI still misses backend mypy, frontend e2e, and keeps backend lint non-blocking.

- Local tooling gap during remediation: `lsp_diagnostics` for TypeScript files is unavailable in this environment because `typescript-language-server` is not installed and global npm install is blocked by permissions (`EACCES`) plus Node engine mismatch warnings.
- Local browser dependency install with `npx playwright install --with-deps chromium` cannot complete in this environment because sudo passwordless elevation is unavailable; fallback `npx playwright install chromium` succeeds for local browser binaries.
