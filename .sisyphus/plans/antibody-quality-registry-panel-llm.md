# Antibody Quality Registry + LLM Context Enrichment Plan

## TL;DR
> **Summary**: Build an end-to-end workflow that captures antibody quality issues in a dedicated registry, organizes them incrementally at save time, and injects the organized context into panel-related LLM prompts as guidance-only information.
> **Deliverables**:
> - Backend persistence + immutable audit history for quality issue records
> - Save-time antibody-level organization/projection layer
> - AI-assisted candidate lookup + user confirmation modal for clone-unknown feedback
> - LLM context enrichment in panel evaluation and marker recommendation flows
> - Backend API contracts and frontend registration/history page
> - TDD coverage across backend/API/prompt assembly + Playwright UI flow
> **Effort**: Large
> **Parallel**: YES - 4 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 3 -> Task 5 -> Task 7 -> Task 8 -> Task 10

## Context
### Original Request
在实验中，存在一部分“不好用”的抗体，希望增加“信息登记 -> 自动整理 -> 筛选 Panel 时将相关信息注入 LLM”的完整流程。

### Interview Summary
- Scope confirmed: backend full workflow + frontend registration page
- Registry requirements confirmed: dedicated table with antibody info, issue text, reporter, timestamps
- Organization granularity confirmed: antibody-level
- Trigger confirmed: save-time incremental organization
- LLM policy confirmed: context-only guidance, no hard filtering
- Prompt strategy confirmed: full relevant context injection (with implementation guardrails)
- Feedback disambiguation confirmed: user may submit marker+color+brand without clone
- Candidate confirmation confirmed: auto-trigger lookup + single-choice modal
- No-match policy confirmed: send to manual review queue
- Testing strategy confirmed: TDD
- Governance confirmed: full audit trail required

### Metis Review (gaps addressed)
- Addressed canonical identity risk by explicitly defining an antibody identity contract task before any organization work
- Addressed storage/audit integrity risk by separating raw records, derived projection, and prompt-ready context models
- Addressed prompt inflation risk with deterministic dedupe + truncation order + token budget checks
- Addressed free-text risk with validation bounds, sanitization, and rendering-safe handling
- Addressed scope creep by declaring non-goals (no moderation/notification/ontology/dashboard in this phase)

## Work Objectives
### Core Objective
Deliver a production-usable quality-registration and context-enrichment workflow that improves panel screening explainability without changing hard filtering behavior.

### Deliverables
- Dedicated backend persistence for antibody quality issue records and immutable history
- Deterministic antibody-level organization/projection for screening consumption
- AI-assisted candidate retrieval and single-select confirmation flow for partial feedback input
- Manual review queue for unresolved candidate matching
- Prompt-context enrichment utilities wired into existing panel/recommendation LLM flows
- API endpoints for create/list/detail/history operations
- Frontend page for registration, listing, and history viewing
- TDD-first automated verification for domain logic, APIs, prompt shaping, and UI flow

### Definition of Done (verifiable conditions with commands)
- `PYTHONPATH=. python -m pytest tests/ -q` passes with new and existing backend tests
- `cd frontend && npx playwright test` passes including new registry flow E2E
- `make check-all` passes
- API tests verify create/list/history contracts and audit fields
- Prompt assembly tests verify inclusion, dedupe, truncation, and deterministic output order

### Must Have
- Dedicated quality registry (not overloaded inventory CSV rows)
- Immutable audit history for all create/update state changes
- Feedback can be submitted without clone by using marker+color+brand inputs
- Auto-trigger candidate lookup from natural language feedback and single-select confirmation modal
- Unresolved feedback is routed into manual review queue with traceable status
- Save-time incremental organization by canonical antibody identity
- Context-only LLM injection in both panel evaluation and marker recommendation paths
- Frontend registration/history workflow with input validation
- Evidence artifacts written under `.sisyphus/evidence/`

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- No hard filtering or automatic exclusion of antibodies in screening output
- No silent auto-binding of candidate antibody without user confirmation
- No taxonomy/ontology management system beyond current free-text requirement
- No notification/approval workflow, moderation console, or analytics dashboard
- No ambiguous “manual verification only” acceptance criteria
- No non-deterministic prompt-shaping behavior without test coverage

## Verification Strategy
> ZERO HUMAN INTERVENTION — all verification is agent-executed.
- Test decision: TDD (RED-GREEN-REFACTOR) with pytest + Playwright
- QA policy: Every task includes agent-executed happy and failure scenarios
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks for max parallelism.

Wave 1: identity and contract foundation (domain model, test harness, API schema skeleton)
Wave 2: persistence + audit + projection core
Wave 3: LLM context shaping + API wiring + frontend integration
Wave 4: hardening (edge cases, performance guardrails, regression)

### Dependency Matrix (full, all tasks)
- Task 1 blocks Tasks 2, 3, 4, 5
- Task 2 blocks Tasks 3, 4
- Task 3 blocks Tasks 5, 7, 8
- Task 4 blocks Task 8
- Task 5 blocks Tasks 6, 7
- Task 6 blocks Task 10
- Task 7 blocks Task 10
- Task 8 blocks Task 9
- Task 9 blocks Task 10
- Task 10 blocks Task 11
- Task 11 blocks Task 12
- Tasks 1, 2, 4 can partially run in parallel within Wave 1 once contracts freeze

### Agent Dispatch Summary (wave -> task count -> categories)
- Wave 1 -> 3 tasks -> deep/quick/unspecified-low
- Wave 2 -> 3 tasks -> deep/unspecified-high
- Wave 3 -> 3 tasks -> visual-engineering/unspecified-high
- Wave 4 -> 3 tasks -> deep/unspecified-high
- Final Verification -> 4 tasks -> oracle/unspecified-high/deep

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [x] 1. Define dual-key identity contracts (feedback key + entity key)

  **What to do**: Define dual identity contracts: (A) feedback submission key `species + normalized_marker + fluorochrome + brand` (clone optional), and (B) canonical entity key `species + normalized_marker + clone + brand + catalog_number` (lot tracked as metadata). Freeze request/response contracts for raw issue record, candidate-match result, manual-review item, organized projection, and prompt-ready context payload.
  **Must NOT do**: Do not force clone in submission; do not couple prompt payload shape to DB internals.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: foundational domain decisions block all downstream implementation
  - Skills: `[]` — Reason: repo-native domain contracts are primary
  - Omitted: `['frontend-design']` — Reason: no UI work in this task

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [2,3,4,5] | Blocked By: []

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `data_preprocessing.py` — marker normalization and alias handling rules
  - Pattern: `backend/app/schemas/panels.py` — Pydantic schema style and validation conventions
  - Pattern: `backend/app/schemas/recommendations.py` — endpoint contract style for recommendation payloads
  - Pattern: `backend/app/core/config.py` — domain config conventions and naming

  **Acceptance Criteria** (agent-executable only):
  - [ ] New schema tests fail first then pass for dual-key generation and payload validation (`PYTHONPATH=. python -m pytest tests/ -q -k "quality_contract or antibody_identity or candidate_match"`)
  - [ ] Canonical identity collision tests cover alias/case/spacing variants
  - [ ] Submission contract accepts missing clone and still produces valid feedback key

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Canonical identity normalization happy path
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "antibody_identity and normalization"`
    Expected: Tests pass and show same identity for equivalent aliases/casing
    Evidence: .sisyphus/evidence/task-1-identity-contracts.txt

  Scenario: Invalid payload rejection
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "quality_contract and invalid"`
    Expected: Validation fails for missing reporter, blank issue text, or malformed antibody fields
    Evidence: .sisyphus/evidence/task-1-identity-contracts-error.txt

  Scenario: Clone-unknown submission accepted
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "feedback_key and clone_optional"`
    Expected: Submission without clone is accepted and emits feedback key for candidate lookup
    Evidence: .sisyphus/evidence/task-1-identity-contracts-clone-optional.txt
  ```

  **Commit**: YES | Message: `test(quality): lock antibody identity and payload contracts` | Files: `tests/**`, `backend/app/schemas/**`

- [x] 2. Implement dedicated registry persistence and immutable audit history

  **What to do**: Add persistence layer for raw quality records and immutable history events; include created/updated metadata and append-only event log semantics for all state transitions.
  **Must NOT do**: Do not write mutable audit rows in place; do not store records inside inventory CSV files.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: backend data layer + migration + constraints
  - Skills: `[]` — Reason: implementation is repo-specific
  - Omitted: `['shadcn']` — Reason: no component work

  **Parallelization**: Can Parallel: PARTIAL | Wave 1 | Blocks: [3,4,7] | Blocked By: [1]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `backend/app/api/v1/endpoints/panels.py` — endpoint-to-domain wiring style
  - Pattern: `tests/api/conftest.py` — API fixture and client setup conventions
  - Pattern: `tests/conftest.py` — test session fixture style

  **Acceptance Criteria** (agent-executable only):
  - [ ] Persistence tests verify create/update operations create immutable history entries (`PYTHONPATH=. python -m pytest tests/ -q -k "quality_registry and audit"`)
  - [ ] Attempting direct history mutation is rejected by tests

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Append-only audit happy path
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "quality_registry and append_only"`
    Expected: Create/update generate additional history events; prior events remain unchanged
    Evidence: .sisyphus/evidence/task-2-registry-audit.txt

  Scenario: Forbidden mutation path
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "quality_registry and history_mutation_forbidden"`
    Expected: Mutation attempt fails with explicit error/exception assertion
    Evidence: .sisyphus/evidence/task-2-registry-audit-error.txt
  ```

  **Commit**: YES | Message: `feat(quality): add registry store with immutable audit history` | Files: `backend/app/**`, `tests/**`

- [x] 3. Build save-time incremental organization/projection at antibody level

  **What to do**: Implement incremental projection logic that updates antibody-level organized quality summary on each record save; include deterministic dedupe and stable ordering.
  **Must NOT do**: Do not run full batch rebuild on every save; do not mix raw free text storage with projection output format.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: deterministic projection logic with identity linkage
  - Skills: `[]` — Reason: existing preprocessing patterns are sufficient
  - Omitted: `['playwright']` — Reason: non-browser backend task

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [5,7,8] | Blocked By: [1,2]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `data_preprocessing.py` — normalization and grouping precedent
  - Pattern: `channel_mapping.json` — stable mapping usage style for deterministic transforms
  - Test: `tests/characterization/test_panel_parity.py` — deterministic algorithm test style

  **Acceptance Criteria** (agent-executable only):
  - [ ] Projection tests pass for add/update dedupe and stable ordering (`PYTHONPATH=. python -m pytest tests/ -q -k "quality_projection"`)
  - [ ] Same-antibody alias variants project into one antibody summary key

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Incremental projection happy path
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "quality_projection and incremental"`
    Expected: New save updates only affected antibody projection and keeps deterministic order
    Evidence: .sisyphus/evidence/task-3-projection.txt

  Scenario: Duplicate issue collapse
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "quality_projection and dedupe"`
    Expected: Duplicate semantically identical entries are collapsed by projection rules
    Evidence: .sisyphus/evidence/task-3-projection-error.txt
  ```

  **Commit**: YES | Message: `feat(quality): add save-time antibody-level projection` | Files: `data_preprocessing.py`, `backend/app/**`, `tests/**`

- [x] 4. Add registry API contracts and endpoint tests first (TDD)

  **What to do**: Define and implement API contracts for create/list/detail/history plus candidate-lookup and manual-review queue endpoints. Candidate lookup must support natural language input (`"APC 的 CD56 有问题"`) and return ranked candidates for single selection.
  **Must NOT do**: Do not auto-bind candidate server-side without explicit user confirmation; do not leave pagination/filter semantics undefined.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: API contract and behavior enforcement
  - Skills: `[]` — Reason: existing FastAPI style is straightforward
  - Omitted: `['fastapi-templates']` — Reason: extending existing service, not greenfield

  **Parallelization**: Can Parallel: PARTIAL | Wave 1/2 bridge | Blocks: [8,9] | Blocked By: [1,2]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `backend/app/api/v1/endpoints/recommendations.py` — endpoint structure and response wrapping style
  - Pattern: `backend/app/api/v1/endpoints/panels.py` — request parsing and error handling style
  - Test: `tests/api/test_health.py` — API assertion style

  **Acceptance Criteria** (agent-executable only):
  - [ ] API tests pass for create/list/detail/history success + validation failures (`PYTHONPATH=. python -m pytest tests/api -q -k "quality_registry"`)
  - [ ] Reporter/timestamp fields present per visibility policy in registry APIs
  - [ ] Candidate lookup API tests pass for clone-unknown inputs and ranked candidate response
  - [ ] No-match API tests route records to manual review queue with status `pending_review`

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Registry create/list/history happy path
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/api -q -k "quality_registry and happy"`
    Expected: POST succeeds; list returns new record; history endpoint shows immutable events
    Evidence: .sisyphus/evidence/task-4-registry-api.txt

  Scenario: Validation failure path
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/api -q -k "quality_registry and invalid_payload"`
    Expected: Invalid payload returns expected 4xx with structured error body
    Evidence: .sisyphus/evidence/task-4-registry-api-error.txt

  Scenario: Candidate lookup and no-match fallback
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/api -q -k "candidate_lookup or manual_review_queue"`
    Expected: Matched inputs return ranked candidates; unmatched inputs enter `pending_review` queue
    Evidence: .sisyphus/evidence/task-4-registry-api-candidate-queue.txt
  ```

  **Commit**: YES | Message: `feat(api): add quality registry endpoints with strict contracts` | Files: `backend/app/api/v1/endpoints/**`, `backend/app/schemas/**`, `tests/api/**`

- [x] 5. Implement prompt-ready quality context formatter with budget guardrails

  **What to do**: Build a deterministic formatter that transforms antibody-level projection into prompt-ready context blocks with dedupe, sanitization, stable sort, and hard token budget (`MAX_QUALITY_CONTEXT_CHARS`/token-estimate threshold).
  **Must NOT do**: Do not inject raw unsanitized free text; do not let context exceed configured budget without truncation metadata.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: deterministic prompt shaping under noisy free-text input
  - Skills: `[]` — Reason: local LLM integration already exists
  - Omitted: `['ai-sdk']` — Reason: this repo uses local client patterns, not AI SDK runtime

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [6,7] | Blocked By: [3]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `panel_generator.py` — prompt assembly in evaluation/recommendation flows
  - Pattern: `llm_api_client.py` — current model invocation boundary
  - Test: `tests/characterization/test_panel_parity.py` — deterministic output test pattern

  **Acceptance Criteria** (agent-executable only):
  - [ ] Formatter tests pass for dedupe/order/sanitization/token-cap behavior (`PYTHONPATH=. python -m pytest tests/ -q -k "quality_context_formatter"`)
  - [ ] Over-budget input emits deterministic truncation marker in formatted context

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Deterministic formatting happy path
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "quality_context_formatter and deterministic"`
    Expected: Same input ordering/content always yields identical formatted context
    Evidence: .sisyphus/evidence/task-5-context-formatter.txt

  Scenario: Prompt budget overflow handling
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "quality_context_formatter and overflow"`
    Expected: Output is truncated/compressed per policy and includes truncation indicator
    Evidence: .sisyphus/evidence/task-5-context-formatter-error.txt
  ```

  **Commit**: YES | Message: `feat(panel-llm): add deterministic quality context formatter` | Files: `panel_generator.py`, `backend/app/**`, `tests/**`

- [x] 6. Inject quality context into panel evaluation LLM path

  **What to do**: Wire formatted quality context into `evaluate_candidates_with_llm()` prompt section as guidance-only content with clear labeling.
  **Must NOT do**: Do not change candidate generation/filtering logic; do not hard fail when context is absent.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: sensitive change to ranking/evaluation path
  - Skills: `[]` — Reason: existing prompt architecture is local
  - Omitted: `['oracle']` — Reason: implementation task, not review task

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: [10] | Blocked By: [5]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `panel_generator.py` — `evaluate_candidates_with_llm()` prompt structure
  - Pattern: `backend/app/api/v1/endpoints/panels.py` — evaluation endpoint integration

  **Acceptance Criteria** (agent-executable only):
  - [ ] Tests confirm prompt contains quality section when relevant context exists (`PYTHONPATH=. python -m pytest tests/ -q -k "panel_evaluate and quality_context"`)
  - [ ] Tests confirm behavior remains valid when no quality context exists

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Quality context injected in evaluate flow
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "panel_evaluate and quality_context_present"`
    Expected: Prompt payload includes labeled quality guidance section
    Evidence: .sisyphus/evidence/task-6-evaluate-injection.txt

  Scenario: No-context fallback
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "panel_evaluate and quality_context_absent"`
    Expected: Evaluation still completes with baseline prompt and no crash
    Evidence: .sisyphus/evidence/task-6-evaluate-injection-error.txt
  ```

  **Commit**: YES | Message: `feat(panel-llm): inject quality context into candidate evaluation` | Files: `panel_generator.py`, `tests/**`

- [x] 7. Inject quality context into marker recommendation LLM path

  **What to do**: Wire formatted quality context into `recommend_markers_from_inventory()` with same contract and budget guardrails as evaluation path.
  **Must NOT do**: Do not diverge context schema between evaluation and recommendation paths.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: second critical LLM path must stay contract-compatible
  - Skills: `[]` — Reason: reuse formatter and prompt contract
  - Omitted: `['vercel-ai-sdk']` — Reason: not used in this code path

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: [10] | Blocked By: [3,5]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `panel_generator.py` — `recommend_markers_from_inventory()` prompt style
  - Pattern: `backend/app/api/v1/endpoints/recommendations.py` — recommendation endpoint payload flow

  **Acceptance Criteria** (agent-executable only):
  - [ ] Tests confirm recommendation prompt includes quality guidance context (`PYTHONPATH=. python -m pytest tests/ -q -k "recommend_markers and quality_context"`)
  - [ ] Context contract parity tests pass between evaluate/recommend paths

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Quality context injected in recommendation flow
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "recommend_markers and quality_context_present"`
    Expected: Recommendation prompt includes same labeled quality context schema
    Evidence: .sisyphus/evidence/task-7-recommend-injection.txt

  Scenario: Contract mismatch prevention
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q -k "quality_context and contract_parity"`
    Expected: Test fails on schema drift and passes when schemas stay aligned
    Evidence: .sisyphus/evidence/task-7-recommend-injection-error.txt
  ```

  **Commit**: YES | Message: `feat(panel-llm): inject quality context into marker recommendation` | Files: `panel_generator.py`, `backend/app/api/v1/endpoints/recommendations.py`, `tests/**`

- [x] 8. Add frontend API client + hook support for quality registry

  **What to do**: Extend frontend API client and hooks to call quality registry, candidate-lookup, candidate-confirm, and manual-review queue endpoints. Support auto-trigger lookup on text input with debounce and cancellable requests.
  **Must NOT do**: Do not bypass centralized API client; do not bury error handling in component-only logic.

  **Recommended Agent Profile**:
  - Category: `quick` — Reason: adaptation of existing client/hook patterns
  - Skills: `[]` — Reason: no new framework requirement
  - Omitted: `['nextjs-app-router-patterns']` — Reason: small integration task

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: [9,10] | Blocked By: [3,4]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `frontend/src/lib/api-client.ts` — API helper patterns and error mapping
  - Pattern: `frontend/src/lib/hooks/use-panel-generation.ts` — hook state and request lifecycle style
  - Pattern: `frontend/src/app/panel-design/page.tsx` — page-layer hook consumption

  **Acceptance Criteria** (agent-executable only):
  - [ ] Playwright spec for registry API client/hook behavior passes (`cd frontend && npx playwright test -g "quality registry api client"`)
  - [ ] Create/list/history success and error states are observable in UI and asserted by test
  - [ ] Auto-trigger lookup hook tests pass for debounce/cancel/retry semantics

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Hook success path
    Tool: Playwright
    Steps: Run `cd frontend && npx playwright test -g "quality registry api client success"`; in test, submit valid form and observe loading->success UI state transitions bound to hook
    Expected: UI reflects hook state transitions idle->loading->success and list refreshes with returned payload
    Evidence: .sisyphus/evidence/task-8-frontend-hooks.txt

  Scenario: Hook error path
    Tool: Playwright
    Steps: Run `cd frontend && npx playwright test -g "quality registry api client error"`; in test, submit invalid payload and mocked 4xx response
    Expected: Structured error UI is displayed and page remains interactive
    Evidence: .sisyphus/evidence/task-8-frontend-hooks-error.txt
  ```

  **Commit**: YES | Message: `feat(frontend): add quality registry api client and hooks` | Files: `frontend/src/lib/**`, `frontend/tests/**`

- [x] 9. Build frontend registration + list + history page

  **What to do**: Implement a dedicated UI route for quality issue registration and history browsing, including natural-language issue input, auto candidate lookup modal, single-select candidate confirmation, and manual-review fallback view; keep deterministic selectors for E2E (`data-testid`).
  **Must NOT do**: Do not merge this into panel-design page; do not ship without accessible labels and validation messaging.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` — Reason: UX + form + history table composition
  - Skills: `[]` — Reason: existing project UI conventions should be followed
  - Omitted: `['shadcn']` — Reason: no requirement to introduce new component dependency

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: [10] | Blocked By: [4,8]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `frontend/src/app/panel-design/page.tsx` — page layout and data flow style
  - Pattern: `frontend/src/app/exp-design/page.tsx` — form interactions and data submissions
  - Pattern: `frontend/src/lib/hooks/use-panel-generation.ts` — async UI state pattern

  **Acceptance Criteria** (agent-executable only):
  - [ ] New page route renders registration form, list view, and history view with test IDs
  - [ ] UI validation prevents empty reporter/issue text and surfaces clear errors
  - [ ] Candidate modal enforces single selection and explicit confirm action
  - [ ] No-match submission appears in manual review tab/status view

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: UI registration happy path
    Tool: Playwright
    Steps: Go to quality page; fill `data-testid=quality-issue-textarea` with "APC 的 CD56 有问题" and reporter; wait auto lookup; in `quality-candidate-modal` select one candidate; click confirm + submit; open `quality-history-panel`
    Expected: Candidate modal appears automatically; single candidate is confirmed; success toast appears; history shows create event and bound candidate
    Evidence: .sisyphus/evidence/task-9-quality-page.png

  Scenario: UI validation failure
    Tool: Playwright
    Steps: Submit with empty reporter and blank issue text; then submit unmatched text to trigger no-match flow
    Expected: Validation errors shown for blank fields; unmatched entry routes to `pending_review` and is visible in review tab
    Evidence: .sisyphus/evidence/task-9-quality-page-error.png
  ```

  **Commit**: YES | Message: `feat(frontend): add quality registry registration and history page` | Files: `frontend/src/app/**`, `frontend/src/components/**`, `frontend/e2e/**`

- [x] 10. Add end-to-end flow tests across backend + UI + prompt integration

  **What to do**: Add integration/E2E tests proving an issue record created in UI/API appears in organized projection and is included in panel/recommendation LLM prompt context.
  **Must NOT do**: Do not assert exact LLM natural-language output; assert context structure and inclusion only.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: cross-layer test orchestration
  - Skills: `['playwright']` — Reason: browser and flow validation
  - Omitted: `['frontend-design']` — Reason: testing, not styling

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: [11,12] | Blocked By: [6,7,8,9]

  **References** (executor has NO interview context — be exhaustive):
  - Test: `frontend/e2e/smoke.spec.ts` — Playwright style and setup
  - Test: `tests/api/test_recommendations.py` — API+LLM boundary testing with mocks
  - Test: `tests/api/test_panels_generate.py` — panel endpoint testing pattern

  **Acceptance Criteria** (agent-executable only):
  - [ ] `cd frontend && npx playwright test -g "quality registry"` passes
  - [ ] Backend integration tests assert quality context section inclusion for both panel evaluate and recommendation flows
  - [ ] E2E test passes for clone-unknown -> candidate confirm -> LLM context propagation
  - [ ] E2E test passes for no-match -> manual review queue path

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: End-to-end context propagation happy path
    Tool: Playwright
    Steps: Submit "APC 的 CD56 有问题" via UI; select one candidate in modal; trigger panel evaluate/recommend workflow; inspect mocked LLM request payload
    Expected: Payload quality section contains selected antibody-bound context with traceable source record
    Evidence: .sisyphus/evidence/task-10-e2e-context.txt

  Scenario: Absent-quality fallback
    Tool: Bash
    Steps: Run integration test with unmatched feedback routed to manual review and no confirmed candidate
    Expected: Workflow succeeds; unresolved item does not break prompt assembly; manual-review status remains queryable
    Evidence: .sisyphus/evidence/task-10-e2e-context-error.txt
  ```

  **Commit**: YES | Message: `test(e2e): cover quality registry to llm context propagation` | Files: `tests/**`, `frontend/e2e/**`

- [x] 11. Harden edge cases: free-text safety, dedupe drift, and concurrency

  **What to do**: Add and pass tests for overlong free text, unicode/special chars, duplicate submissions, same-antibody concurrent saves, and deterministic projection after race-like updates.
  **Must NOT do**: Do not rely on best-effort behavior; every edge case must have explicit expected outcome.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: reliability and correctness under hostile/realistic inputs
  - Skills: `[]` — Reason: domain test depth is primary
  - Omitted: `['dev-browser']` — Reason: backend reliability focus

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: [12] | Blocked By: [10]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `tests/conftest.py` — deterministic setup conventions
  - Pattern: `data_preprocessing.py` — normalization edge surfaces
  - Pattern: `panel_generator.py` — prompt assembly edge surfaces

  **Acceptance Criteria** (agent-executable only):
  - [ ] Edge-case regression suite passes (`PYTHONPATH=. python -m pytest tests/ -q -k "quality and edge"`)
  - [ ] Concurrency/idempotency tests pass for repeated identical save requests
  - [ ] Candidate ranking tie-break tests pass with deterministic order
  - [ ] Auto-trigger lookup debounce tests pass under rapid typing

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Free-text safety happy path
    Tool: Bash
    Steps: Run tests with long and special-character issue text payloads
    Expected: Input stored safely, prompt context sanitized/escaped, UI render remains stable
    Evidence: .sisyphus/evidence/task-11-edge-hardening.txt

  Scenario: Concurrent duplicate submit
    Tool: Bash
    Steps: Run concurrent request test for same antibody and issue text
    Expected: Projection remains deterministic; duplicates handled per dedupe policy
    Evidence: .sisyphus/evidence/task-11-edge-hardening-error.txt
  ```

  **Commit**: YES | Message: `test(quality): add edge and concurrency hardening coverage` | Files: `tests/**`, `backend/app/**`

- [x] 12. Final integration gate and quality evidence packaging

  **What to do**: Execute full suite (`test-backend`, target e2e, `check-all`), collect evidence artifacts, and verify all Must Have / Must NOT Have constraints map to automated checks.
  **Must NOT do**: Do not close task with partial test runs; do not skip failing suites.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: final cross-system validation and evidence collation
  - Skills: `[]` — Reason: relies on existing commands and artifacts
  - Omitted: `['momus']` — Reason: Momus is optional post-plan review path

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: [] | Blocked By: [10,11]

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `Makefile` — canonical test and check commands
  - Pattern: `.sisyphus/evidence/` — evidence artifact location convention

  **Acceptance Criteria** (agent-executable only):
  - [ ] `make test-backend` passes
  - [ ] `cd frontend && npx playwright test -g "quality registry"` passes
  - [ ] `make check-all` passes
  - [ ] Evidence files exist for Tasks 1-11

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Full verification happy path
    Tool: Bash
    Steps: Run `make test-backend && cd frontend && npx playwright test -g "quality registry" && cd .. && make check-all`
    Expected: All commands exit 0 and evidence artifacts are generated for each task
    Evidence: .sisyphus/evidence/task-12-final-gate.txt

  Scenario: Regression gate failure path
    Tool: Bash
    Steps: Intentionally run with a failing edge test fixture in CI-like mode
    Expected: Gate fails fast and reports failing suite with actionable test identifier
    Evidence: .sisyphus/evidence/task-12-final-gate-error.txt
  ```

  **Commit**: YES | Message: `chore(quality): finalize verification gate and evidence bundle` | Files: `.sisyphus/evidence/**`, `tests/**`, `frontend/e2e/**`

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [x] F1. Plan Compliance Audit — oracle
- [x] F2. Code Quality Review — unspecified-high
- [x] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [x] F4. Scope Fidelity Check — deep

## Commit Strategy
- `test(quality-registry): add failing specs for identity, audit, and prompt context contracts`
- `feat(quality-registry): implement persistence, projection, and API contracts`
- `feat(panel-llm): inject quality context into evaluation and recommendation prompts`
- `feat(frontend): add quality registration and history page with API integration`
- `test(regression): add edge-case and performance guardrail coverage`

## Success Criteria
- New workflow is discoverable and executable end-to-end from UI/API to LLM context usage
- Clone-unknown feedback is supported via marker+color+brand input with AI-assisted candidate confirmation
- Unmatched feedback reliably enters manual review queue with full traceability
- Screening recommendations include structured quality context without changing hard selection semantics
- Auditability guarantees are test-verified for all mutating actions
- Regression suite demonstrates deterministic behavior under duplicate/long/free-text issue inputs
