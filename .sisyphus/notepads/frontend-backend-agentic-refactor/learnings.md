- Added first pytest characterization baseline under `tests/characterization` using existing Python modules as oracle without changing domain logic.
- Locked observed parsing behavior where `normalize_marker_name()` strips trailing `a`/`b`, including aliases like `LCA -> lc` during `parse_target_aliases()`.
- Captured panel solver invariants: uniqueness of `system_code` per panel, scarcity-first assignment order (observable through dict insertion order), and `max_solutions` capping.
- Added impossible-set fixture and diagnosis assertion to preserve current no-solution messaging with explicit conflict group, marker names, and contested channel.
- 5. Created FastAPI skeleton under `backend/app/` with versioned router at `/api/v1`. Package uses `backend.app.main:app` as ASGI entry point — import path includes `backend.` prefix because the package lives inside the repo root (not installed as a library).
- 6. Pyright reports `reportMissingImports` for `backend.app.*` and `pytest_asyncio` — this is a Pyright configuration issue (no `pyproject.toml` with `extraPaths`), not a runtime problem. `python -m pytest` and `uvicorn` both resolve imports correctly via `sys.path` which includes project root.
- 7. `pytest-asyncio` requires `@pytest_asyncio.fixture` for async fixtures (not `@pytest.fixture`). Using `@pytest.fixture` on an async generator triggers `PytestRemovedIn9Warning` and the fixture won't be handled.
- 8. Settings defaults mirror existing `llm_api_client.py` env var names exactly: `OPENAI_API_BASE`, `OPENAI_API_KEY`, `OPENAI_MODEL_NAME`. Default model changed from `gpt-oss-20b` (AGENTS.md) to `Qwen3-14B` (actual `llm_api_client.py` default).
- 9. CORS allows `localhost:3000` (Next.js dev) and `localhost:8501` (Streamlit dev). No auth or database deps added — keeping skeleton minimal for Tasks 3-5.
- 10. httpx `ASGITransport` is the modern way to test FastAPI apps (replaces deprecated `TestClient` pattern for async). Async test client fixture lives in `tests/api/conftest.py`.
- Task 3 integration note: `/api/v1/panels/generate` can wrap existing `generate_candidate_panels()` directly, then normalize output into stable DTO fields by adding `target` and preserving unique `system_code` values per candidate.
- Task 3 integration note: `/api/v1/panels/diagnose` must normalize input markers before `diagnose_conflicts()` because `aggregate_antibodies_by_marker()` keys are normalized aliases.
- Task 4 (spectra endpoint): `POST /api/v1/spectra/render-data` returns chart-ready Gaussian data series. Uses `importlib.import_module("spectral_viewer")` to call `get_gaussian_curve()` directly, preserving exact Gaussian semantics. Case-insensitive fluorochrome matching mirrors `spectral_viewer.py` strategy. `x_range = np.linspace(350, 900, 550)` matches original Plotly viewer. Unknown fluorochromes go to `warnings` list without crashing. 7 new tests added (23 total pass).

- Added POST /api/v1/recommendations/markers and POST /api/v1/panels/evaluate wrappers that call existing panel_generator LLM domain functions without duplicating parsing logic.
- Preserved evaluation malformed-output fallback behavior by passing through evaluate_candidates_with_llm() and validating via API tests that Option 1 is selected when LLM output is invalid.
- Added API tests with mocked consult_gpt_oss for success, malformed-response fallback, and exception paths; full suite now passes with PYTHONPATH=. python -m pytest tests/ -q.


## Task 2: Frontend Scaffold Complete

### Summary
- Initialized shadcn/ui with `npx shadcn@latest init -d` (Tailwind 4, Next.js 16 compatible)
- Installed AI SDK dependencies: `ai`, `@ai-sdk/openai`
- Installed shadcn components: `button`, `input`, `card`, `tabs`, `badge`
- Created parity shell pages matching Streamlit tab structure:
  - `/exp-design` — Experimental Design page shell
  - `/panel-design` — Panel Generation page shell
  - `/` — Home/landing page with navigation

### Pages Created

**Home Page** (`src/app/page.tsx`):
- Project description and navigation cards
- Links to both Experimental Design and Panel Generation
- "How It Works" section explaining Search-Evaluate-Visualize workflow

**Experimental Design** (`src/app/exp-design/page.tsx`):
- Research goal text area
- Number of colors slider (1-30)
- Species selector (Mouse/Human)
- "Recommend Markers" button placeholder
- Recommended markers table placeholder
- "Use This Panel" action button placeholder

**Panel Generation** (`src/app/panel-design/page.tsx`):
- Marker input with default sample markers
- Species selector
- "Search Panels" button placeholder
- Candidate panels with Tabs for multiple options
- AI Evaluation section with recommendation and gating strategy placeholders
- Spectral visualization placeholder area
- Conflict diagnosis placeholder area

### Technical Details

**Dependencies Added** (verified in package.json):
- `ai@^6.0.140` — Vercel AI SDK
- `@ai-sdk/openai@^3.0.48` — OpenAI provider
- `@base-ui/react@^1.3.0` — shadcn primitives
- `class-variance-authority`, `clsx`, `tailwind-merge`, `tw-animate-css` — utilities
- `lucide-react@^1.7.0` — icon library

**API Client** (`src/lib/api-client.ts`):
- Simple fetch wrapper pointing to `NEXT_PUBLIC_API_URL`
- Prefixes all calls with `/api/v1`
- Generic `get`, `post`, `put`, `delete` methods

**Environment** (`frontend/.env.local`):
- `NEXT_PUBLIC_API_URL=http://localhost:8000`

**Layout** (`src/app/layout.tsx`):
- Updated title: "FlowCyt Panel Assistant"
- Navigation header with links to /, /exp-design, /panel-design
- Footer with project description

### Verification
- `npm run lint --prefix frontend` — exits 0 (no errors, only warnings fixed)
- `npx tsc --noEmit --project frontend/tsconfig.json` — exits 0 (no type errors)

### Notes
- All pages use Client Components (`"use client"`) for interactivity
- shadcn components properly imported via `@/components/ui/*` aliases
- Streamlit tab structure faithfully replicated as separate Next.js App Router pages
- Placeholder sections ready for actual API integration in Task 8

# Frontend Integration Implementation

## Completed Tasks

### 1. Created use-marker-recommendation.ts hook
- Path: frontend/src/lib/hooks/use-marker-recommendation.ts
- Pattern: Follows the same pattern as use-panel-generation.ts
- State: { markers, markersDetail, isLoading, error }
- Method: recommend(experimentalGoal, numColors, species)
- Maps species display names to API params (Mouse/Human)

### 2. Updated Exp Design page (exp-design/page.tsx)
- Integrated useMarkerRecommendation hook
- Added API call to POST /recommendations/markers
- Displays markers table with Marker | Type | Rationale columns
- Added loading and error states
- Added "Use This Panel" button that navigates to /panel-design with markers URL param
- Added Clear button to reset state

### 3. Created spectra-chart.tsx component
- Path: frontend/src/components/spectra-chart.tsx
- Uses recharts library (LineChart, ResponsiveContainer, etc.)
- Props: fluorochromes: string[]
- Fetches data from /spectra/render-data API
- Renders multi-line chart with proper colors from API
- X axis: Wavelength (nm), Y axis: Normalized Intensity (%)
- Shows warnings for unknown fluorochromes
- Loading and error states handled

### 4. Updated Panel Design page (panel-design/page.tsx)
- Reads markers from URL search params on mount
- Pre-fills markers input from URL params
- Auto-triggers search if markers provided via URL
- Replaced spectral placeholder with SpectraChart component
- Chart updates when different candidate tab is selected
- Extracts fluorochromes from selected candidate
- Removed unused getBrightnessStars variable

### 5. Dependencies
- Installed recharts library for spectral visualization

## API Integration Summary

### Exp Design -> Panel Design Flow
1. User fills experiment config in /exp-design
2. "Recommend Markers" calls POST /recommendations/markers
3. Results displayed in table
4. "Use This Panel" navigates to /panel-design?markers=CD3,CD4,...
5. Panel Design page reads markers and auto-searches

### Spectral Chart
1. When candidate tab selected, extract fluorochromes
2. SpectraChart receives fluorochromes prop
3. Component fetches from POST /spectra/render-data
4. Renders Gaussian emission curves with proper colors


## Task: Fullstack CI Quality Gates

- Created `Makefile` with 7 targets: test-backend, lint-backend, lint-frontend, typecheck-frontend, generate-client, check-drift, check-all.
- lint-backend gracefully skips if ruff not installed (no new Python deps).
- Created `.github/workflows/ci.yml` with 3 parallel jobs: backend (pytest), frontend (lint+typecheck), client-drift (generate+diff check).
- Uses Python 3.11 and Node 20 in CI; npm cache keyed on frontend/package-lock.json.
- Existing Gemini AI workflows (.github/workflows/gemini-*.yml) left untouched.
- Created `PARITY_GATE.md` with 4 sections (API Parity, UI Parity, Data Flow Parity, Quality Gates) — 27 checkbox items total with verification commands.
- `make check-all` passes: 28 backend tests, frontend lint clean, typecheck clean, client in sync.

- Manual QA on 2026-03-27: backend smoke endpoints all returned `status: success`/healthy responses against `tests/fixtures/panel_inventory.csv`; panel generation returned 6 valid candidates, diagnosis returned the expected advisory message, and spectra render returned 3 chart series for FITC/PE/APC.
- Verification commands all passed end-to-end: `PYTHONPATH=. python -m pytest tests/ -v` (28/28), `npx tsc --noEmit`, `npm run lint`, `npm run generate:client`, `npm run check:client-drift`, and `make check-all`.
- Domain files `panel_generator.py`, `data_preprocessing.py`, `spectral_viewer.py`, `llm_api_client.py`, and `streamlit_app.py` showed no diff in `git diff HEAD~10 -- ...`; working tree only contains unrelated untracked repo metadata files.

- 2026-03-27 scope audit: domain Python files (`panel_generator.py`, `data_preprocessing.py`, `spectral_viewer.py`, `llm_api_client.py`, `streamlit_app.py`) stayed untouched across commits `636d9f7..70e3866`, so the canonical solver/preprocessing/spectral logic was not rewritten during the refactor wave.

- Code review learning: backend/Frontend contract currently encodes many business failures inside `200 OK` bodies with `status: "error"`; this forces every hook to duplicate semantic-error handling and already caused frontend inconsistency.
- Code review learning: allowing caller-supplied `inventory_file` absolute or repo-relative paths creates a local file access surface that should be constrained before exposing the FastAPI layer beyond trusted local development.

## 2026-03-27 Plan Compliance Audit
- Backend parity wrappers correctly preserve canonical Python domain logic by importing existing modules instead of rewriting solver, normalization, diagnosis, or spectral math.
- Generated OpenAPI types are present and current; npm run generate:client, npm run check:client-drift, frontend lint, frontend typecheck, and PYTHONPATH=. python -m pytest tests/ all pass locally.
- Streamlit has not been retired; PARITY_GATE.md exists as an explicit cutover checklist artifact.

- Final verification remediation: `_resolve_inventory_path()` now rejects path traversal/separators and only resolves filenames under `inventory/`, removing absolute/repo-relative access branches in both panel and recommendation endpoints.
- Final verification remediation: FastAPI endpoints now raise `HTTPException(status_code=400, detail=...)` for business/runtime failures, and frontend hooks explicitly guard `data.status === "error"` to avoid treating semantic failures as success states.
- Test adaptation pattern: with inventory path hardening, API tests now stage fixture CSVs into `inventory/` and pass basename-only `inventory_file` values; non-success API responses are asserted via HTTP status code and `detail` payload.

- Scope-fidelity distinction: vague Playwright scenario details are aspirational, but the executable e2e command in plan DoD and Tasks 8-9 acceptance criteria is concrete and therefore binding.

- Round 2 final verification remediation: species input is now sanitized for path traversal in both `_resolve_inventory_path()` implementations before species-based filename resolution.
- Backend species routing now derives filenames from `Settings.SPECIES_INVENTORY_MAP` with case-insensitive matching and `{species}.csv` fallback, removing frontend filename coupling.
- Characterization coverage now includes explicit multi-encoding CSV load behavior (`utf-8`, `gbk`, `gb18030`, `latin1`) plus a GBK fixture under `tests/fixtures/gbk_inventory.csv`.
- Frontend inventory selection now sends species-only intent (`inventory_file: null`) so backend config remains the single source of truth for inventory filenames.
- CI quality gates now include blocking backend ruff lint and a dedicated frontend Playwright smoke test job.
- 2026-03-27 F1 Round 4 final audit: species now flows through diagnose end-to-end (`DiagnoseRequest.species`, `diagnose_panels(... payload.species)`, and frontend diagnose body uses `speciesParam`), resolving the prior multi-inventory path selection bug.
