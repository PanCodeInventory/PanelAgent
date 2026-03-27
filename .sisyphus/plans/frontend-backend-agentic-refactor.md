# Agentic Frontend Backend Refactor

## TL;DR
> **Summary**: Migrate the Streamlit monolith to Next.js App Router + FastAPI with parity-first execution, keeping Python domain logic canonical and preserving all scientific constraints.
> **Deliverables**:
> - Versioned FastAPI backend (`/api/v1`) wrapping current Python logic
> - Next.js frontend with parity workflows and AI SDK integration
> - OpenAPI-generated typed TS client
> - Full quality gates (tests/lint/typecheck/e2e/contract drift)
> **Effort**: XL
> **Parallel**: YES - 2 waves
> **Critical Path**: 1 -> 2 -> 3 -> 6 -> 8 -> 9 -> 10

## Context
### Original Request
基于前后端重构，给出详细规划，并为 agentic 方向做好框架与技术路径。

### Interview Summary
- Preserve 3 core outcomes:
  - non-duplicate panel generation
  - spectral visualization
  - inventory-driven AI recommendation/evaluation
- Replace Streamlit UI with modern frontend stack.
- Use project-level skills already installed (`ai-sdk`, `fastapi-templates`, `nextjs-app-router-*`, `shadcn`).

### Metis Review (gaps addressed)
- Added strict parity-first migration order.
- Added OpenAPI-first contract governance.
- Added characterization tests before refactor.
- Added LLM malformed output fallback checks.
- Added anti-scope-creep guardrails.

## Work Objectives
### Core Objective
Deliver a decision-complete execution plan for frontend/backend migration with zero ambiguity for implementers.

### Deliverables
- FastAPI service boundary for all current core capabilities.
- Next.js parity UI for Exp Design and Panel Gen flows.
- Stable API schema + generated frontend client.
- CI quality baseline replacing current no-gate state.

### Definition of Done (verifiable conditions with commands)
- `python -m pytest` exits 0.
- `python -m ruff check .` exits 0.
- `python -m mypy .` exits 0.
- `npm run lint --prefix frontend` exits 0.
- `npm run typecheck --prefix frontend` exits 0.
- `npm run test:e2e --prefix frontend` exits 0.
- `npm run generate:client --prefix frontend && git diff --exit-code` exits 0.

### Must Have
- Preserve no-duplicate-`System_Code` invariant.
- Preserve alias-aware matching and normalization behavior.
- Preserve conflict diagnosis for unsat marker sets.
- Preserve CSV encoding fallback behavior.
- Keep Python domain logic canonical in migration phase.

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- No TypeScript rewrite of solver/preprocessing/spectral math.
- No direct frontend dependence on pandas/internal dict shapes.
- No Streamlit retirement before parity gates pass.
- No parallel expansion into auth/billing/queue/replatform extras.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: characterization-first + tests-after per migration task.
- Backend: `pytest` with golden fixtures.
- Frontend: Playwright e2e parity scenarios.
- Contracts: OpenAPI snapshot + generated client drift check.
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
Wave 1: backend parity foundation (Tasks 1-5)
Wave 2: frontend parity integration (Tasks 6-10)

### Dependency Matrix (full, all tasks)
- 1 blocks 2,3,4,5,6,7,8,9,10
- 2 blocks 3,4,5,7,8,9,10
- 3 blocks 8,9,10
- 4 blocks 9,10
- 5 blocks 9,10
- 6 blocks 7,8,9,10
- 7 blocks 8,9,10
- 8 blocks 9,10
- 9 blocks 10
- 10 blocks Final Verification Wave

### Agent Dispatch Summary (wave -> task count -> categories)
- Wave 1 -> 5 tasks -> deep / unspecified-high / quick
- Wave 2 -> 5 tasks -> visual-engineering / unspecified-high / deep
- Final verification -> 4 tasks -> oracle / unspecified-high / deep

## TODOs
> Implementation + Test = ONE task. Never separate.

- [x] 1. Characterization Baseline Lock

  **What to do**: Add characterization fixtures/tests for normalization, alias mapping, panel generation uniqueness, and no-solution diagnosis using current modules as oracle.
  **Must NOT do**: Do not modify domain logic.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: invariants must be frozen before extraction.
  - Skills: [`fastapi-templates`] - for test/app skeleton conventions.
  - Omitted: [`visual-engineering`] - no UI scope.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 2-10 | Blocked By: none

  **References**:
  - `panel_generator.py:8`
  - `panel_generator.py:52`
  - `data_preprocessing.py:5`
  - `data_preprocessing.py:24`
  - `data_preprocessing.py:49`

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/characterization -q` exits 0.
  - [ ] Includes alias-heavy, impossible-set, and multi-encoding fixtures.
  - [ ] At least one test asserts unique `system_code` in every candidate.

  **QA Scenarios**:
  ```text
  Scenario: Happy path characterization
    Tool: Bash
    Steps: Run `python -m pytest tests/characterization/test_panel_parity.py -q`
    Expected: Pass; includes unique System_Code assertion
    Evidence: .sisyphus/evidence/task-1-characterization.txt

  Scenario: Failure/edge no-solution
    Tool: Bash
    Steps: Run `python -m pytest tests/characterization/test_no_solution.py -q`
    Expected: Structured diagnosis assertion passes
    Evidence: .sisyphus/evidence/task-1-characterization-error.txt
  ```

  **Commit**: YES | Message: `test(characterization): lock current domain behavior` | Files: [`tests/characterization/**`, `tests/fixtures/**`]

- [x] 2. FastAPI Skeleton and API Versioning

  **What to do**: Create backend app package, `/api/v1` routers, settings, CORS, and health endpoint.
  **Must NOT do**: No algorithm rewrite.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: API foundation for all migration tasks.
  - Skills: [`fastapi-templates`]
  - Omitted: [`shadcn`]

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 3-5,7-10 | Blocked By: 1

  **References**:
  - `llm_api_client.py:14`
  - `streamlit_app.py:36`
  - `https://fastapi.tiangolo.com/reference/apirouter/`
  - `https://fastapi.tiangolo.com/tutorial/cors/`

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/api/test_health.py -q` exits 0.
  - [ ] `curl` to `/api/v1/health` returns status JSON.

  **QA Scenarios**:
  ```text
  Scenario: Happy path API boot
    Tool: Bash
    Steps: Start uvicorn and call `/api/v1/health`
    Expected: HTTP 200 with status payload
    Evidence: .sisyphus/evidence/task-2-fastapi.txt

  Scenario: Failure/edge CORS invalid origin
    Tool: Bash
    Steps: Send preflight with disallowed Origin
    Expected: No permissive CORS headers
    Evidence: .sisyphus/evidence/task-2-fastapi-error.txt
  ```

  **Commit**: YES | Message: `feat(api): add fastapi v1 skeleton` | Files: [`backend/**`]

- [x] 3. Panel Generation and Diagnosis Endpoints

  **What to do**: Implement `POST /api/v1/panels/generate` and `POST /api/v1/panels/diagnose` wrapping existing modules with stable DTOs.
  **Must NOT do**: No changes to scarcity-first solver behavior or uniqueness logic.

  **Recommended Agent Profile**:
  - Category: `deep`
  - Skills: [`fastapi-templates`]
  - Omitted: [`ai-sdk`]

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 8-10 | Blocked By: 1,2

  **References**:
  - `panel_generator.py:102`
  - `panel_generator.py:8`
  - `panel_generator.py:52`
  - `data_preprocessing.py:133`

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/api/test_panels_generate.py -q` exits 0.
  - [ ] `python -m pytest tests/api/test_panels_diagnose.py -q` exits 0.

  **QA Scenarios**:
  ```text
  Scenario: Happy path generation
    Tool: Bash
    Steps: POST valid fixture markers to generate endpoint
    Expected: Non-empty candidates, each with unique `system_code`
    Evidence: .sisyphus/evidence/task-3-panels.txt

  Scenario: Failure/edge impossible set
    Tool: Bash
    Steps: POST impossible fixture to diagnose endpoint
    Expected: Structured conflict diagnosis returned
    Evidence: .sisyphus/evidence/task-3-panels-error.txt
  ```

  **Commit**: YES | Message: `feat(api): add panel generation and diagnosis endpoints` | Files: [`backend/app/routers/panels.py`, `backend/app/schemas/**`, `tests/api/**`]

- [x] 4. Spectral Render Data Endpoint

  **What to do**: Add `POST /api/v1/spectra/render-data` returning chart-ready data series while preserving Gaussian semantics.
  **Must NOT do**: No spectral constant/formula changes.

  **Recommended Agent Profile**:
  - Category: `unspecified-high`
  - Skills: [`fastapi-templates`]
  - Omitted: [`nextjs-app-router-patterns`]

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 9,10 | Blocked By: 2

  **References**:
  - `spectral_viewer.py:14`
  - `spectral_viewer.py:25`
  - `spectral_data.json`

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/api/test_spectra.py -q` exits 0.
  - [ ] Fixture peak alignment assertions pass.

  **QA Scenarios**:
  ```text
  Scenario: Happy path spectra payload
    Tool: Bash
    Steps: POST valid panel to spectra endpoint
    Expected: Series arrays and color metadata present
    Evidence: .sisyphus/evidence/task-4-spectra.txt

  Scenario: Failure/edge unknown fluorochrome
    Tool: Bash
    Steps: POST panel with unknown fluorochrome
    Expected: Graceful warning/error response, no crash
    Evidence: .sisyphus/evidence/task-4-spectra-error.txt
  ```

  **Commit**: YES | Message: `feat(api): add spectra render-data endpoint` | Files: [`backend/app/routers/spectra.py`, `tests/api/test_spectra.py`]

- [x] 5. Recommendation and Evaluation Endpoints

  **What to do**: Add `POST /api/v1/recommendations/markers` and `POST /api/v1/panels/evaluate` with preserved malformed-output fallback chain.
  **Must NOT do**: No removal of JSON parsing fallbacks.

  **Recommended Agent Profile**:
  - Category: `deep`
  - Skills: [`ai-sdk`]
  - Omitted: [`shadcn`]

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 9,10 | Blocked By: 2

  **References**:
  - `panel_generator.py:165`
  - `panel_generator.py:308`
  - `llm_api_client.py:14`
  - `https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling`

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/api/test_recommendations.py -q` exits 0.
  - [ ] `python -m pytest tests/api/test_evaluation_fallbacks.py -q` exits 0.

  **QA Scenarios**:
  ```text
  Scenario: Happy path recommendation
    Tool: Bash
    Steps: POST goal+inventory context to recommendation endpoint
    Expected: `selected_markers` and `markers_detail` returned
    Evidence: .sisyphus/evidence/task-5-recommend.txt

  Scenario: Failure/edge malformed LLM output
    Tool: Bash
    Steps: Mock malformed LLM response in evaluation tests
    Expected: Stable fallback response, no 500
    Evidence: .sisyphus/evidence/task-5-recommend-error.txt
  ```

  **Commit**: YES | Message: `feat(api): add recommendation and evaluation endpoints` | Files: [`backend/app/routers/recommendations.py`, `backend/app/routers/evaluations.py`, `tests/api/**`]

- [x] 6. Next.js App Router Frontend Shell

  **What to do**: Scaffold frontend app, install AI SDK + shadcn, create parity shell for Exp Design and Panel Gen, and explicit client state model replacing Streamlit session state.
  **Must NOT do**: No direct calls to legacy Python files from frontend.

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: [`nextjs-app-router-patterns`, `nextjs-app-router-fundamentals`, `shadcn`]
  - Omitted: [`fastapi-templates`]

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 7-10 | Blocked By: 1

  **References**:
  - `streamlit_app.py:91`
  - `streamlit_app.py:140`
  - `https://nextjs.org/docs/app/building-your-application/routing/route-handlers`
  - `https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat`

  **Acceptance Criteria**:
  - [ ] `npm run lint --prefix frontend` exits 0.
  - [ ] `npm run typecheck --prefix frontend` exits 0.

  **QA Scenarios**:
  ```text
  Scenario: Happy path shell render
    Tool: Playwright
    Steps: Open app and verify Exp Design + Panel Gen regions
    Expected: Both regions visible and controls interactive
    Evidence: .sisyphus/evidence/task-6-shell.png

  Scenario: Failure/edge bad API URL
    Tool: Playwright
    Steps: Launch with invalid backend URL
    Expected: User-facing error state without crash
    Evidence: .sisyphus/evidence/task-6-shell-error.png
  ```

  **Commit**: YES | Message: `feat(frontend): scaffold app router parity shell` | Files: [`frontend/**`]

- [x] 7. OpenAPI Typed Client Generation

  **What to do**: Implement OpenAPI -> TS client generation and drift enforcement.
  **Must NOT do**: No handwritten duplicate DTOs.

  **Recommended Agent Profile**:
  - Category: `quick`
  - Skills: [`nextjs-app-router-patterns`]
  - Omitted: [`visual-engineering`]

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 8-10 | Blocked By: 2,6

  **References**:
  - `https://fastapi.tiangolo.com/advanced/generate-clients/`
  - `https://github.com/ferdikoomen/openapi-typescript-codegen`

  **Acceptance Criteria**:
  - [ ] `npm run generate:client --prefix frontend` exits 0.
  - [ ] `npm run check:client-drift --prefix frontend` exits 0.

  **QA Scenarios**:
  ```text
  Scenario: Happy path client generation
    Tool: Bash
    Steps: Generate client and run typecheck
    Expected: Generated client compiles and endpoints typed
    Evidence: .sisyphus/evidence/task-7-client.txt

  Scenario: Failure/edge schema drift
    Tool: Bash
    Steps: Desync schema then run drift check
    Expected: Non-zero exit with clear diff message
    Evidence: .sisyphus/evidence/task-7-client-error.txt
  ```

  **Commit**: YES | Message: `chore(api-client): add generated typed client workflow` | Files: [`frontend/src/lib/api/**`, `frontend/package.json`]

- [x] 8. Panel Generation Parity UI

  **What to do**: Build panel input/search/candidate display and diagnosis UX using typed client.
  **Must NOT do**: No generic fallback replacing diagnosis details.

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: [`shadcn`, `nextjs-app-router-patterns`]
  - Omitted: [`fastapi-templates`]

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 9,10 | Blocked By: 3,6,7

  **References**:
  - `streamlit_app.py:195`
  - `streamlit_app.py:242`
  - `streamlit_app.py:226`

  **Acceptance Criteria**:
  - [ ] `npm run test:e2e --prefix frontend -- --grep "panel generation parity"` exits 0.
  - [ ] Impossible fixture shows diagnosis panel.

  **QA Scenarios**:
  ```text
  Scenario: Happy path panel generation UI
    Tool: Playwright
    Steps: Fill markers and trigger search
    Expected: Candidate options rendered
    Evidence: .sisyphus/evidence/task-8-panel-ui.png

  Scenario: Failure/edge impossible markers UI
    Tool: Playwright
    Steps: Submit impossible fixture markers
    Expected: Conflict diagnosis visible
    Evidence: .sisyphus/evidence/task-8-panel-ui-error.png
  ```

  **Commit**: YES | Message: `feat(frontend): implement panel generation parity ui` | Files: [`frontend/src/components/panel/**`, `frontend/tests/e2e/**`]

- [x] 9. Exp Design + Evaluation + Spectra Integration

  **What to do**: Implement recommendation flow, "Use This Panel" transfer, evaluation action, rationale/gating display, and spectra chart integration.
  **Must NOT do**: No frontend-side parsing of raw LLM strings.

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: [`ai-sdk`, `shadcn`]
  - Omitted: [`fastapi-templates`]

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 10 | Blocked By: 4,5,8

  **References**:
  - `streamlit_app.py:145`
  - `streamlit_app.py:188`
  - `streamlit_app.py:257`
  - `streamlit_app.py:292`
  - `spectral_viewer.py:25`

  **Acceptance Criteria**:
  - [ ] `npm run test:e2e --prefix frontend -- --grep "exp design to panel gen transfer"` exits 0.
  - [ ] `npm run test:e2e --prefix frontend -- --grep "ai evaluation and spectra"` exits 0.

  **QA Scenarios**:
  ```text
  Scenario: Happy path full UX chain
    Tool: Playwright
    Steps: Recommend markers -> use panel -> evaluate -> view spectra
    Expected: Transfer works; rationale/gating/spectra render
    Evidence: .sisyphus/evidence/task-9-agentic-ui.png

  Scenario: Failure/edge evaluation fallback
    Tool: Playwright
    Steps: Mock fallback evaluation response and trigger evaluate
    Expected: Stable UI fallback state, no crash
    Evidence: .sisyphus/evidence/task-9-agentic-ui-error.png
  ```

  **Commit**: YES | Message: `feat(frontend): integrate exp design evaluation and spectra` | Files: [`frontend/src/components/exp-design/**`, `frontend/src/components/evaluation/**`, `frontend/src/components/spectra/**`]

- [x] 10. Quality Gates and Cutover Controls

  **What to do**: Add fullstack CI checks (backend/frontend/e2e/client drift), and explicit parity gate checklist before Streamlit decommission.
  **Must NOT do**: No legacy removal prior to parity approvals.

  **Recommended Agent Profile**:
  - Category: `unspecified-high`
  - Skills: [`fastapi-templates`, `nextjs-app-router-patterns`]
  - Omitted: [`shadcn`]

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: Final Verification | Blocked By: 1-9

  **References**:
  - `.github/workflows/`
  - `Dockerfile`
  - `README.md:42`

  **Acceptance Criteria**:
  - [ ] CI runs backend tests/lint/typecheck and frontend lint/type/e2e.
  - [ ] Client drift check enforced in CI.
  - [ ] Streamlit retirement gated by parity checklist artifact.

  **QA Scenarios**:
  ```text
  Scenario: Happy path full pipeline
    Tool: Bash
    Steps: Run local CI-equivalent scripts
    Expected: All checks pass
    Evidence: .sisyphus/evidence/task-10-quality.txt

  Scenario: Failure/edge forced drift
    Tool: Bash
    Steps: Intentionally desync generated client and run checks
    Expected: Drift gate fails with actionable output
    Evidence: .sisyphus/evidence/task-10-quality-error.txt
  ```

  **Commit**: YES | Message: `ci(migration): add parity gates and cutover controls` | Files: [`.github/workflows/**`, `frontend/package.json`, `backend/**`]

## Final Verification Wave (MANDATORY - after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.
> Never mark F1-F4 as checked before getting user's okay. Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [x] F1. Plan Compliance Audit - oracle
- [x] F2. Code Quality Review - unspecified-high
- [x] F3. Real Manual QA - unspecified-high (+ playwright if UI)
- [x] F4. Scope Fidelity Check - deep

## Commit Strategy
- One atomic commit per task.
- Conventional commits required.
- Mandatory sequence checkpoints:
  - characterization baseline before extraction
  - API schema + generated client before UI integration
  - Streamlit retirement only after parity + final verification approval

## Success Criteria
- Next.js + FastAPI implementation reproduces core outputs and workflows.
- All invariants remain intact.
- CI quality gates are green.
- No unresolved architectural decisions remain for executors.
