# Docker LAN Compose Migration

## TL;DR
> **Summary**: Package the current Next.js + FastAPI app into a Docker Compose stack for LAN serving without touching the live tmux stack until Docker passes full validation on alternate ports.
> **Deliverables**:
> - Production-style `Dockerfile` for backend
> - Production-style `Dockerfile` for frontend
> - `docker-compose.yml` for staged LAN validation
> - Minimal config changes for container-safe env/CORS/path handling
> - Validation + rollback runbook with agent-executable checks
> **Effort**: Medium
> **Parallel**: YES - 2 waves
> **Critical Path**: T1 -> T2 -> T4 -> T6 -> F1-F4

## Context
### Original Request
Create a Docker migration plan while keeping the current tmux-hosted app running. Do not migrate traffic until the Docker path is proven safe.

### Interview Summary
- Current live setup is acceptable and must remain untouched during planning and validation.
- Docker is being evaluated as a more stable LAN-serving mode for classmates.
- Existing browser-facing interface should remain the same.
- User specifically asked how `.env` and mutable app data should work under Docker.

### Metis Review (gaps addressed)
- Use alternate validation ports; do not touch current `3000`/`8000` during validation.
- Treat `data/quality_registry/` as authoritative mutable state with explicit mount strategy.
- Keep scope limited to Docker Compose viability plus only the minimum app changes required for container correctness.
- Add rollback rehearsal and concrete cutover gates.

## Work Objectives
### Core Objective
Stand up a Docker Compose deployment path for PanelAgent that preserves the current LAN-facing interface model, persists mutable data safely, and can be validated end-to-end before any cutover from tmux.

### Deliverables
- Backend container build definition
- Frontend container build definition
- Compose topology with internal service networking and alternate validation ports
- Env strategy documenting host-side `.env` ownership and container injection
- Volume strategy for mutable and reference data
- Validation and rollback procedure

### Definition of Done (verifiable conditions with commands)
- `docker compose -f docker-compose.yml config` exits 0
- `docker compose -f docker-compose.yml build` exits 0
- `docker compose -f docker-compose.yml up -d` starts the staged stack on alternate ports only
- `curl http://127.0.0.1:18000/api/v1/health` returns JSON containing `"status":"ok"`
- `curl -I http://127.0.0.1:13000` returns `200 OK`
- A browser automation check against `http://127.0.0.1:13000` loads the current UI and completes one API-backed flow
- A quality-registry write survives `docker compose restart backend`
- Stopping the staged Compose stack leaves the existing tmux stack reachable on `:3000` and `:8000`

### Must Have
- Keep current tmux services running until Docker validation passes
- Validate Docker stack on alternate ports: frontend `13000`, backend `18000`
- Preserve frontend entrypoint behavior for classmates (`host:3000` at eventual cutover)
- Keep backend API path shape `/api/v1/*`
- Persist `data/quality_registry/` outside the container filesystem
- Use host-side env files; do not bake secrets into images
- Add healthchecks and restart policy suitable for LAN service mode

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- Must NOT stop, replace, or reuse the live tmux ports during validation
- Must NOT introduce Kubernetes, Swarm, or external orchestration
- Must NOT migrate persistence away from file-backed JSON storage
- Must NOT redesign the app into a new routing model unless required for container correctness
- Must NOT rely on `next dev` as the final LAN-serving Docker runtime
- Must NOT store mutable production data only inside containers
- Must NOT require manual user clicking as acceptance evidence

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after + existing Pytest + browser automation + curl
- QA policy: Every task includes executable validation steps
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. Extract shared dependencies first.

Wave 1: runtime/container foundations (`config`, `docker`, `validation`)
Wave 2: staged validation, persistence, rollback, documentation

### Dependency Matrix (full, all tasks)
- T1 blocks T2, T3, T4
- T2 blocks T5 and T6
- T3 blocks T6
- T4 blocks T6
- T5 blocks T7
- T6 blocks T7
- T7 blocks F1-F4

### Agent Dispatch Summary (wave -> task count -> categories)
- Wave 1 -> 4 tasks -> `unspecified-high`, `quick`
- Wave 2 -> 3 tasks -> `unspecified-high`, `writing`
- Final Verification -> 4 tasks -> `oracle`, `unspecified-high`, `deep`

## TODOs
> Implementation + Test = ONE task. Never separate.

- [x] 1. Freeze Current Runtime Contract

  **What to do**: Document the exact live contract that Docker must preserve: frontend entrypoint, backend health endpoint, env file ownership, repo-root data path expectations, and authoritative mutable-state paths. Record the validation ports (`13000` frontend, `18000` backend) and the rule that live tmux ports `3000/8000` remain untouched until cutover.
  **Must NOT do**: Do not modify runtime behavior yet. Do not stop tmux services. Do not invent new public URLs.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: cross-cutting deployment facts must be gathered and locked
  - Skills: `[]` - no special skill needed
  - Omitted: `frontend-design` - unrelated

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T2, T3, T4 | Blocked By: none

  **References**:
  - Pattern: `frontend/next.config.ts:21` - frontend currently proxies `/api/v1/*`
  - API/Type: `backend/app/api/v1/endpoints/health.py:8` - health endpoint to preserve in Docker
  - API/Type: `backend/app/core/config.py:15` - backend env loading from host `.env`
  - Pattern: `backend/app/services/quality_registry_store.py:95` - mutable runtime data path

  **Acceptance Criteria**:
  - [ ] A deployment contract section is added to the migration docs/runbook listing live ports, validation ports, env ownership, and persistent paths
  - [ ] `curl http://127.0.0.1:8000/api/v1/health` returns `{"status":"ok","version":"1.0.0"}` before any Docker work begins

  **QA Scenarios**:
  ```text
  Scenario: Confirm live baseline contract
    Tool: Bash
    Steps: Run `curl -s http://127.0.0.1:8000/api/v1/health` and `curl -sI http://127.0.0.1:3000`
    Expected: Backend returns status ok JSON; frontend returns HTTP 200 headers
    Evidence: .sisyphus/evidence/task-1-runtime-contract.txt

  Scenario: Confirm mutable data path exists
    Tool: Bash
    Steps: Run `ls data/quality_registry && ls data/quality_registry/audit && ls data/quality_registry/projections`
    Expected: All three paths exist and are readable
    Evidence: .sisyphus/evidence/task-1-runtime-contract-data.txt
  ```

  **Commit**: YES | Message: `docs(deploy): define docker migration runtime contract` | Files: `.sisyphus/*` or deployment docs only

- [x] 2. Add Backend Production Container

  **What to do**: Create a backend Dockerfile that runs FastAPI/Uvicorn in production mode on `0.0.0.0:8000`, uses repo-root-aware working directory so config path resolution continues to work, loads env from Compose injection, and can read mounted data/inventory/reference files. Add a backend healthcheck command that uses `/api/v1/health`.
  **Must NOT do**: Do not use reload mode. Do not assume localhost-only binding. Do not bake secrets into the image.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: container filesystem and Python path correctness matter
  - Skills: `[]`
  - Omitted: `fastapi-templates` - current app already exists; avoid broad scaffold changes

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: T5, T6 | Blocked By: T1

  **References**:
  - Pattern: `backend/app/main.py:28` - FastAPI app entrypoint
  - API/Type: `backend/app/core/config.py:54` - repo-root path resolution must remain valid
  - Pattern: `backend/app/services/quality_registry_store.py:95` - mounted data path must be writable
  - Test: `tests/test_config_static_paths.py` - path-resolution expectations

  **Acceptance Criteria**:
  - [ ] Backend image builds via `docker build -f Dockerfile.backend -t panelagent-backend .`
  - [ ] Container started with mounted data and env returns health on `18000`
  - [ ] `data/quality_registry/` writes succeed inside the container without path errors

  **QA Scenarios**:
  ```text
  Scenario: Backend health in container
    Tool: Bash
    Steps: Start backend container on host port 18000; run `curl -s http://127.0.0.1:18000/api/v1/health`
    Expected: JSON contains `"status":"ok"`
    Evidence: .sisyphus/evidence/task-2-backend-health.txt

  Scenario: Backend missing volume fails clearly
    Tool: Bash
    Steps: Start backend container without `data/quality_registry` mount; call one quality-registry write endpoint
    Expected: Failure is logged clearly or path creation occurs in expected container path; no silent host-data mismatch
    Evidence: .sisyphus/evidence/task-2-backend-volume-failure.txt
  ```

  **Commit**: YES | Message: `chore(docker): add backend production container` | Files: `Dockerfile.backend`, optional helper scripts/docs

- [x] 3. Add Frontend Production Container

  **What to do**: Create a frontend Dockerfile using a production build flow (`next build` plus production runtime). Configure container runtime so the app listens on `0.0.0.0:3000` and uses `BACKEND_INTERNAL_URL=http://backend:8000` inside Compose. Preserve the current `/api/v1/*` browser behavior.
  **Must NOT do**: Do not use `next dev` as the target LAN-serving runtime. Do not force classmates to use a different public path.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: Next build/runtime split and env behavior must be handled correctly
  - Skills: `[]`
  - Omitted: `nextjs-app-router-patterns` - avoid broad app-router rewrites

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: T6 | Blocked By: T1

  **References**:
  - Pattern: `frontend/package.json:6` - current dev/prod scripts
  - Pattern: `frontend/next.config.ts:25` - rewrite target contract
  - API/Type: `frontend/src/lib/api-client.ts:1` - public/runtime API base handling

  **Acceptance Criteria**:
  - [ ] Frontend image builds via `docker build -f Dockerfile.frontend -t panelagent-frontend ./frontend`
  - [ ] Container started on host port `13000` returns `200 OK`
  - [ ] API-backed frontend requests reach backend through internal Compose networking

  **QA Scenarios**:
  ```text
  Scenario: Frontend loads on alternate port
    Tool: Bash
    Steps: Start frontend container on host port 13000 and run `curl -sI http://127.0.0.1:13000`
    Expected: HTTP 200 response from Next frontend
    Evidence: .sisyphus/evidence/task-3-frontend-head.txt

  Scenario: Misconfigured backend URL fails visibly
    Tool: Bash
    Steps: Start frontend container with an invalid `BACKEND_INTERNAL_URL`, trigger an API-backed page action
    Expected: Request fails with visible API/network error, not a hanging request
    Evidence: .sisyphus/evidence/task-3-frontend-bad-backend.txt
  ```

  **Commit**: YES | Message: `chore(docker): add frontend production container` | Files: `Dockerfile.frontend`, optional nginx/runtime config

- [x] 4. Make Container-Safe Runtime Config Minimal and Explicit

  **What to do**: Introduce only the minimum app changes needed for container correctness: env-driven backend CORS origins, container-safe host binding assumptions, and clear separation between host-side `.env` ownership and container runtime injection. If path assumptions need tightening, do so without changing app semantics.
  **Must NOT do**: Do not refactor unrelated config. Do not redesign the API interface. Do not move data files unless tests prove it necessary.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: small config changes with high deployment impact
  - Skills: `[]`
  - Omitted: `fastapi-templates` - too broad

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: T6 | Blocked By: T1

  **References**:
  - Pattern: `backend/app/main.py:35` - current hardcoded CORS origins need Docker/LAN-safe configuration
  - API/Type: `backend/app/core/config.py:21` - existing env model to extend
  - Test: `tests/test_cwd_independence.py` - preserve path safety

  **Acceptance Criteria**:
  - [ ] Backend CORS origins are configurable by env rather than hardcoded localhost-only values
  - [ ] Existing non-Docker local run still works with current `.env`
  - [ ] No existing path-resolution regression is introduced

  **QA Scenarios**:
  ```text
  Scenario: Container-safe config with live defaults
    Tool: Bash
    Steps: Run targeted config tests and start backend locally with existing env
    Expected: Tests pass and local health endpoint still returns ok
    Evidence: .sisyphus/evidence/task-4-config-defaults.txt

  Scenario: LAN-origin request allowed when configured
    Tool: Bash
    Steps: Send a request with `Origin: http://192.168.1.100:13000` against the staged backend
    Expected: Response includes matching CORS headers when env includes that origin
    Evidence: .sisyphus/evidence/task-4-cors-lan.txt
  ```

  **Commit**: YES | Message: `refactor(config): make docker runtime settings env-driven` | Files: backend config/CORS files and tests only

- [x] 5. Compose the Staged LAN Stack on Alternate Ports

  **What to do**: Add `docker-compose.yml` for a two-service staged stack using internal service DNS (`backend`) and alternate host ports (`13000:3000`, `18000:8000`). Add restart policies, healthchecks, env injection, and explicit mounts for `data/quality_registry/`. Keep backend optionally unpublished internally if frontend proxying is sufficient for staged verification.
  **Must NOT do**: Do not bind to live ports `3000/8000`. Do not couple Compose startup to the tmux stack.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: service networking, healthcheck, and mount correctness all meet here
  - Skills: `[]`
  - Omitted: `proxy-manager` - unrelated

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: T7 | Blocked By: T2

  **References**:
  - Pattern: `frontend/next.config.ts:25` - `BACKEND_INTERNAL_URL` should resolve to Compose service name
  - Pattern: `backend/app/api/v1/endpoints/health.py:8` - backend healthcheck target
  - Pattern: `backend/app/services/quality_registry_store.py:95` - required persistent mount
  - External: Docker Compose docs - `restart: unless-stopped`, service-name DNS, bind/named volumes

  **Acceptance Criteria**:
  - [ ] `docker compose config` exits 0
  - [ ] `docker compose build` exits 0
  - [ ] `docker compose up -d` brings up healthy frontend and backend containers on alternate ports
  - [ ] `docker compose ps` shows both services running and healthy

  **QA Scenarios**:
  ```text
  Scenario: Compose stack comes up cleanly
    Tool: Bash
    Steps: Run `docker compose up -d`, then `docker compose ps` and `docker compose logs --no-color`
    Expected: Both services are running; no startup crash loops
    Evidence: .sisyphus/evidence/task-5-compose-up.txt

  Scenario: Healthcheck catches a broken backend
    Tool: Bash
    Steps: Break backend env intentionally and run `docker compose up -d`
    Expected: Backend becomes unhealthy or exits; Compose/logs make the fault obvious
    Evidence: .sisyphus/evidence/task-5-compose-health-failure.txt
  ```

  **Commit**: YES | Message: `chore(docker): add compose stack for staged lan validation` | Files: `docker-compose.yml`, optional env examples

- [ ] 6. Prove End-to-End UI, API, and Persistence Parity

  **What to do**: Validate the staged Docker stack against the current interface expectations. Run backend tests as needed, then use browser automation against `http://127.0.0.1:13000` to verify the UI loads and at least one API-backed flow completes. Create or mutate a quality-registry record through the API/UI, restart the backend container, and verify the record persists. Capture evidence.
  **Must NOT do**: Do not accept “containers are up” as sufficient. Do not require manual user checks.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: mixed API/UI/persistence validation
  - Skills: `[]`
  - Omitted: `frontend-design` - not relevant

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: T7 | Blocked By: T2, T3, T4

  **References**:
  - Pattern: `frontend/src/lib/hooks/use-panel-generation.ts:71` - API-backed flow to validate
  - API/Type: `backend/app/api/v1/endpoints/quality_registry.py` - persistence surface
  - Test: `tests/api/test_quality_registry.py` - existing persistence expectations

  **Acceptance Criteria**:
  - [ ] Browser automation loads the staged frontend and completes one panel-generation or quality-registry flow successfully
  - [ ] `curl http://127.0.0.1:18000/api/v1/health` returns healthy JSON while Compose stack is up
  - [ ] A created quality issue remains present after `docker compose restart backend`

  **QA Scenarios**:
  ```text
  Scenario: UI flow works through staged frontend
    Tool: Playwright / browser automation
    Steps: Open `http://127.0.0.1:13000`, navigate to one API-backed page, submit known test data, wait for success state
    Expected: No console fatal errors; expected response renders in UI
    Evidence: .sisyphus/evidence/task-6-ui-flow.png

  Scenario: Persistence survives container restart
    Tool: Bash
    Steps: POST a quality-registry issue to staged backend, restart backend container, GET the same issue or list endpoint
    Expected: Created record still exists after restart
    Evidence: .sisyphus/evidence/task-6-persistence-restart.txt
  ```

  **Commit**: YES | Message: `test(deploy): validate compose ui api and persistence parity` | Files: validation scripts/tests/evidence helpers only

- [ ] 7. Add Rollback Runbook and Controlled Cutover Procedure

  **What to do**: Write the exact operational steps for validation, rollback, and eventual cutover. Include backup instructions for `data/quality_registry/`, the explicit rule that tmux remains primary until approval, the command sequence to stop staged Docker safely, and the later cutover step that rebinds Docker to `3000/8000` only after all checks pass.
  **Must NOT do**: Do not actually cut over. Do not stop tmux services. Do not promise zero-risk without a tested rollback.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: deterministic operator runbook
  - Skills: `[]`
  - Omitted: `readme` - avoid broad docs expansion

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: F1-F4 | Blocked By: T5, T6

  **References**:
  - Pattern: `backend/app/services/quality_registry_store.py:91` - backup target path
  - Pattern: live tmux contract from T1 - rollback target remains the tmux stack
  - External: Docker Compose operational guidance for restart and logs

  **Acceptance Criteria**:
  - [ ] Runbook contains backup, validation, rollback, and cutover sections with executable commands
  - [ ] Rollback rehearsal is performed against the staged stack and confirms tmux stack remains reachable

  **QA Scenarios**:
  ```text
  Scenario: Rollback rehearsal preserves live tmux service
    Tool: Bash
    Steps: Stop staged Compose stack, then run `curl -s http://127.0.0.1:8000/api/v1/health` and `curl -sI http://127.0.0.1:3000`
    Expected: Live tmux backend and frontend remain reachable on original ports
    Evidence: .sisyphus/evidence/task-7-rollback.txt

  Scenario: Backup target is usable
    Tool: Bash
    Steps: Archive `data/quality_registry/`, list resulting archive, and verify source files remain untouched
    Expected: Backup artifact exists and source directory contents are unchanged
    Evidence: .sisyphus/evidence/task-7-backup.txt
  ```

  **Commit**: YES | Message: `docs(deploy): add staged docker validation and rollback runbook` | Files: deployment docs/runbook only

## Final Verification Wave (MANDATORY - after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.
- [ ] F1. Plan Compliance Audit - oracle
- [ ] F2. Code Quality Review - unspecified-high
- [ ] F3. Real Manual QA - unspecified-high (+ playwright if UI)
- [ ] F4. Scope Fidelity Check - deep

## Commit Strategy
- `chore(docker): add backend production container`
- `chore(docker): add frontend production container`
- `refactor(config): make docker runtime settings env-driven`
- `chore(docker): add compose stack for staged lan validation`
- `test(deploy): validate compose ui api and persistence parity`
- `docs(deploy): add staged docker validation and rollback runbook`

## Success Criteria
- Docker Compose stack runs on alternate ports without disturbing the tmux stack
- Frontend still serves the same classmate-facing interface model
- Backend remains reachable through frontend proxying and direct health checks
- Quality-registry data survives container restart through mounted persistence
- Rollback is proven before any cutover is attempted
