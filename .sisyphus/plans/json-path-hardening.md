# JSON Path Hardening and Config Unification

## TL;DR
> **Summary**: Fix the CWD-dependent JSON loading bug in `panel_generator.py` and enforce config-backed JSON path resolution as the single runtime source of truth, without package migration.
> **Deliverables**:
> - CWD-independent brightness JSON loading in panel generation flow
> - Centralized JSON path resolution helper in backend config layer
> - Endpoint/test path usage aligned to config-backed resolution
> - Regression tests proving behavior and preventing path regressions
> **Effort**: Short
> **Parallel**: YES - 2 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 3 -> Task 5 -> Task 7 -> Task 8

## Context
### Original Request
- Keep current architecture (no full package migration), but perform two adjustments: fix the hardcoded JSON-path bug and unify JSON path management.

### Interview Summary
- User explicitly chose to execute only the first two high-value changes from earlier analysis:
  - fix `panel_generator.py` hardcoded relative JSON open
  - centralize JSON path management through `backend/app/core/config.py`
- User explicitly did not request domain/module relocation at this stage.

### Metis Review (gaps addressed)
- Guard against scope creep: no package migration, no file moves, no broad cleanup.
- Keep production runtime fix atomic; treat script `__main__` literals as optional unless directly required.
- Require TDD evidence for changed-CWD behavior (red -> green) and config-backed resolution.
- Ensure patch-string tests and endpoint behavior remain stable after refactor.

## Work Objectives
### Core Objective
- Eliminate runtime dependence on process CWD for loading JSON data used in panel generation, and standardize JSON path resolution through backend config-level logic.

### Deliverables
- Config-level resolver for static data paths in `backend/app/core/config.py`.
- Refactored `panel_generator.py` JSON loading path (no bare relative open).
- Endpoint consumers aligned to shared config-backed path resolution pattern.
- Tests updated/added for CWD-independence and centralized path behavior.
- Evidence artifacts for each task in `.sisyphus/evidence/`.

### Definition of Done (verifiable conditions with commands)
- `pytest tests -k "panel and path" -q` exits 0 and includes new CWD/path regression coverage.
- `pytest tests/api/test_panels_generate.py tests/api/test_recommendations.py tests/api/test_spectra.py -q` exits 0.
- `PYTHONPATH=. python -m pytest tests/characterization/test_multi_encoding.py tests/characterization/test_alias.py -q` exits 0.
- `PYTHONPATH=. python -m pytest tests/ -q` exits 0.
- `grep -R "open('fluorochrome_brightness.json'" panel_generator.py` returns no runtime-path usage in panel generation flow.

### Must Have
- Runtime JSON path resolution is config-backed and absolute from project root.
- `panel_generator.generate_candidate_panels` works when CWD is not project root.
- Existing API behaviors remain unchanged (status/message contracts preserved).
- Tests include both happy and failure scenarios for path resolution.

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- Must NOT move modules into `backend/app/domain/` in this plan.
- Must NOT move JSON data files into `backend/app/data/` in this plan.
- Must NOT rewrite unrelated imports, CI, frontend, or packaging.
- Must NOT silently alter response schemas/messages unrelated to path logic.
- Must NOT "pass tests" by weakening assertions or deleting failing tests.
- Must NOT modify `data_preprocessing.py::__main__` or `spectral_viewer.py` defaults unless a failing runtime regression test proves they are required for this scope.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: **TDD** (RED-GREEN-REFACTOR) with `pytest`.
- QA policy: Every task includes executable happy + failure scenarios.
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.txt` (or `-error.txt`).

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. Shared dependencies are front-loaded.

Wave 1: Path bug containment and core resolver foundation (Tasks 1-4)
- T1 regression red test for CWD bug
- T2 config-level static path resolver + unit coverage
- T3 panel generator integration to resolver + green tests
- T4 explicit failure-path behavior test (missing brightness file)

Wave 2: Unification rollout and regression hardening (Tasks 5-8)
- T5 endpoint modules align to shared resolver pattern
- T6 test fixtures/path references align to config-backed source-of-truth
- T7 cross-flow CWD-independence regression suite
- T8 full backend verification and evidence consolidation

### Dependency Matrix (full, all tasks)
- T1: Blocks T3, T7
- T2: Blocks T3, T5, T6
- T3: Blocked by T1, T2; blocks T7, T8
- T4: Blocked by T3; blocks T8
- T5: Blocked by T2; blocks T8
- T6: Blocked by T2; blocks T8
- T7: Blocked by T1, T3; blocks T8
- T8: Blocked by T3, T4, T5, T6, T7

### Agent Dispatch Summary (wave -> task count -> categories)
- Wave 1 -> 4 tasks -> `unspecified-low`, `quick`
- Wave 2 -> 4 tasks -> `unspecified-low`, `quick`
- Final Verification Wave -> 4 tasks -> `oracle`, `unspecified-high`, `deep`

## TODOs
> Implementation + Test = ONE task. Never separate.

- [x] 1. Add RED regression for CWD-dependent brightness JSON loading

  **What to do**: Create `tests/test_json_path_resolution.py` with test `test_generate_candidate_panels_is_cwd_independent` that executes panel generation while running pytest from `/tmp`; first run must fail pre-fix due to relative brightness JSON loading.
  **Must NOT do**: Do not modify production code in this task.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: focused test-only change with deterministic repro.
  - Skills: [] - no extra skill required.
  - Omitted: [`git-commit`] - commit handling is orchestration-level.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [3, 7] | Blocked By: []

  **References**:
  - Pattern: `tests/test_panel_evaluate_quality.py:21` - existing import/use of panel evaluation entrypoint.
  - Pattern: `tests/test_panel_recommend_quality.py:21` - existing panel-generator oriented test structure.
  - API/Type: `panel_generator.py:272` - current hardcoded brightness JSON open call.
  - Test: `tests/api/test_panels_generate.py` - API flow around generation.

  **Acceptance Criteria**:
  - [ ] New regression test runs from non-project-root CWD and fails pre-fix due to path issue.
  - [ ] Regression test is isolated and deterministic (no network/LLM dependence).
  - [ ] Evidence captures red-state output.

  **QA Scenarios** (MANDATORY):
  ```text
  Scenario: Happy path (RED reproduction captured)
    Tool: Bash
    Steps: Run `PYTHONPATH=/home/user/PanChongshi/Repo/PanelAgent python -m pytest /home/user/PanChongshi/Repo/PanelAgent/tests/test_json_path_resolution.py::test_generate_candidate_panels_is_cwd_independent -q` with working directory `/tmp` before production fix
    Expected: Fails with path-related error tied to brightness JSON resolution
    Evidence: .sisyphus/evidence/task-1-cwd-red.txt

  Scenario: Failure/edge case (false-positive prevention)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/test_json_path_resolution.py::test_generate_candidate_panels_is_cwd_independent -q` from repo root before production fix
    Expected: Error signature differs or does not reproduce CWD-specific failure mode
    Evidence: .sisyphus/evidence/task-1-cwd-red-error.txt
  ```

  **Commit**: YES | Message: `test(paths): add cwd regression for panel brightness loading` | Files: [`tests/**`]

- [x] 2. Add centralized static-data path resolver in config layer with tests

  **What to do**: Introduce helper(s) in `backend/app/core/config.py` (for example `project_root()` + `resolve_static_data_path(name: str) -> Path`) and add `tests/test_config_static_paths.py` with absolute-path and missing-file contract tests.
  **Must NOT do**: Must not move JSON files or alter environment variable contract.

  **Recommended Agent Profile**:
  - Category: `unspecified-low` - Reason: small core-config enhancement with moderate blast radius.
  - Skills: [] - no special skill needed.
  - Omitted: [`fastapi-templates`] - no scaffolding or framework setup needed.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [3, 5, 6] | Blocked By: []

  **References**:
  - Pattern: `backend/app/core/config.py:25` - existing static data settings constants.
  - Pattern: `backend/app/api/v1/endpoints/panels.py:65` - existing root + settings path composition.
  - Pattern: `backend/app/api/v1/endpoints/spectra.py:24` - current static data load pattern.
  - Test: `tests/api/test_spectra.py` - validates spectral data-driven output contracts.

  **Acceptance Criteria**:
  - [ ] Config helper returns absolute path for each static JSON setting.
  - [ ] Helper behavior is covered by unit tests, including missing-file edge handling contract.
  - [ ] Existing settings fields remain backward-compatible.

  **QA Scenarios** (MANDATORY):
  ```text
  Scenario: Happy path (resolver outputs expected absolute path)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/test_config_static_paths.py::test_resolve_static_data_path_returns_absolute_path -q`
    Expected: Passes; resolved paths point to expected project-root JSON files
    Evidence: .sisyphus/evidence/task-2-config-resolver.txt

  Scenario: Failure/edge case (missing file)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/test_config_static_paths.py::test_resolve_static_data_path_missing_file_contract -q`
    Expected: Returns expected failure contract (e.g., explicit exception or empty fallback per design)
    Evidence: .sisyphus/evidence/task-2-config-resolver-error.txt
  ```

  **Commit**: YES | Message: `refactor(config): add static data path resolver helpers` | Files: [`backend/app/core/config.py`, `tests/**`]

- [x] 3. Refactor panel generator brightness JSON loading to use config resolver

  **What to do**: Replace direct relative open usage in panel generation flow with config-backed absolute path resolution. Ensure behavior remains graceful when brightness JSON is absent (existing fallback semantics preserved).
  **Must NOT do**: Must not alter panel scoring logic, candidate ranking logic, or LLM prompt behavior.

  **Recommended Agent Profile**:
  - Category: `unspecified-low` - Reason: targeted production behavior fix with regression risk.
  - Skills: []
  - Omitted: [`ultrabrain`] - complexity is moderate and local.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [7, 8] | Blocked By: [1, 2]

  **References**:
  - API/Type: `panel_generator.py:272` - hardcoded relative path to replace.
  - Pattern: `backend/app/api/v1/endpoints/panels.py:64` - upstream load path flow.
  - Pattern: `backend/app/core/config.py:26` - channel mapping constant style to follow.
  - Test: `tests/test_panel_evaluate_quality.py:21` - evaluation path coverage.

  **Acceptance Criteria**:
  - [ ] No bare relative open remains in panel generation runtime path.
  - [ ] CWD-independent regression test from Task 1 now passes.
  - [ ] Existing panel generation/evaluation tests continue to pass.

  **QA Scenarios** (MANDATORY):
  ```text
  Scenario: Happy path (GREEN after refactor)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/test_json_path_resolution.py::test_generate_candidate_panels_is_cwd_independent tests/test_panel_evaluate_quality.py -q`
    Expected: Former red regression now passes; no behavioral regressions in quality evaluate tests
    Evidence: .sisyphus/evidence/task-3-panel-generator-green.txt

  Scenario: Failure/edge case (brightness file missing)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/test_json_path_resolution.py::test_generate_candidate_panels_missing_brightness_fallback_contract -q`
    Expected: Function follows explicit fallback behavior without crashing unrelated flows
    Evidence: .sisyphus/evidence/task-3-panel-generator-missing-brightness.txt
  ```

  **Commit**: YES | Message: `fix(panel): resolve brightness json via centralized config path` | Files: [`panel_generator.py`, `backend/app/core/config.py?`, `tests/**`]

- [x] 4. Add explicit negative-path contract tests for brightness resolution

  **What to do**: Add dedicated tests ensuring malformed/missing brightness path behavior is deterministic and documented (no hidden CWD dependency).
  **Must NOT do**: Do not loosen assertions to make tests pass.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: test-only contract hardening.
  - Skills: []
  - Omitted: [`readme`] - no documentation rewrite needed.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [8] | Blocked By: [3]

  **References**:
  - Pattern: `tests/api/test_evaluation.py:65` - mocking pattern style.
  - Pattern: `tests/api/test_recommendations.py:21` - paired patch context usage.
  - Test: `tests/test_quality_e2e_integration.py:125` - robust patch/fixture strategy.

  **Acceptance Criteria**:
  - [ ] At least one explicit missing-file negative test exists for brightness resolution.
  - [ ] Assertion validates specific error/fallback contract rather than generic pass.
  - [ ] Test output captured in evidence files.

  **QA Scenarios** (MANDATORY):
  ```text
  Scenario: Happy path (negative contract executes)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/test_json_path_resolution.py::test_generate_candidate_panels_missing_brightness_fallback_contract -q`
    Expected: Test passes and confirms deterministic contract for missing file case
    Evidence: .sisyphus/evidence/task-4-negative-contract.txt

  Scenario: Failure/edge case (unexpected exception type)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/test_json_path_resolution.py::test_generate_candidate_panels_missing_brightness_fallback_contract_strictness -q`
    Expected: Test fails with assertion mismatch, proving contract is strict
    Evidence: .sisyphus/evidence/task-4-negative-contract-error.txt
  ```

  **Commit**: YES | Message: `test(panel): harden missing brightness path contracts` | Files: [`tests/**`]

- [x] 5. Unify endpoint static-data path usage via shared config-backed resolver

  **What to do**: Refactor endpoint modules to consume the shared resolver/helper where they currently duplicate root+settings static path composition.
  **Must NOT do**: Must not change endpoint request/response schemas or status codes.

  **Recommended Agent Profile**:
  - Category: `unspecified-low` - Reason: multi-file but mechanical backend consistency refactor.
  - Skills: []
  - Omitted: [`fastapi-templates`] - existing app remains unchanged.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [8] | Blocked By: [2]

  **References**:
  - Pattern: `backend/app/api/v1/endpoints/panels.py:66` - static mapping path usage.
  - Pattern: `backend/app/api/v1/endpoints/recommendations.py:61` - duplicated mapping path usage.
  - Pattern: `backend/app/api/v1/endpoints/spectra.py:26` - spectral DB path usage.
  - Pattern: `backend/app/api/v1/endpoints/quality_registry.py:115` - mapping path usage.

  **Acceptance Criteria**:
  - [ ] Endpoint modules no longer duplicate ad-hoc static data path join logic where helper applies.
  - [ ] API tests for panels/recommendations/spectra remain green.
  - [ ] No API contract drift in success/error payloads.

  **QA Scenarios** (MANDATORY):
  ```text
  Scenario: Happy path (API regression)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/api/test_panels_generate.py tests/api/test_recommendations.py tests/api/test_spectra.py -q`
    Expected: All selected API tests pass with unchanged response contracts
    Evidence: .sisyphus/evidence/task-5-endpoint-unification.txt

  Scenario: Failure/edge case (invalid inventory input)
    Tool: Bash
    Steps: Run targeted invalid-input API tests in panels/recommendations suite
    Expected: Existing 400/validation behavior remains unchanged
    Evidence: .sisyphus/evidence/task-5-endpoint-unification-error.txt
  ```

  **Commit**: YES | Message: `refactor(api): reuse centralized static path resolver` | Files: [`backend/app/api/v1/endpoints/*.py`, `tests/api/**`]

- [x] 6. Align test fixtures and JSON path references to centralized settings constants

  **What to do**: Update tests that hardcode JSON file names/paths to derive expected path via config constants/resolver so test source-of-truth matches runtime source-of-truth.
  **Must NOT do**: Must not weaken fixture realism or remove coverage.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: test-fixture alignment and low-complexity edits.
  - Skills: []
  - Omitted: [`git-commit`] - commit orchestration remains external.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [8] | Blocked By: [2]

  **References**:
  - Pattern: `tests/conftest.py:22` - hardcoded channel mapping path.
  - Pattern: `tests/conftest.py:28` - hardcoded brightness path.
  - Pattern: `tests/characterization/test_multi_encoding.py:15` - hardcoded mapping path.
  - API/Type: `backend/app/core/config.py:26` - settings constants source-of-truth.

  **Acceptance Criteria**:
  - [ ] Test fixtures resolve JSON paths through centralized settings logic.
  - [ ] Characterization fixtures still load inventory/mapping correctly.
  - [ ] No test depends on ambient CWD for JSON path resolution.

  **QA Scenarios** (MANDATORY):
  ```text
  Scenario: Happy path (fixture alignment)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/characterization/test_multi_encoding.py tests/characterization/test_alias.py tests/characterization/test_normalization.py -q`
    Expected: Fixture-loading tests pass with centralized path usage
    Evidence: .sisyphus/evidence/task-6-fixture-alignment.txt

  Scenario: Failure/edge case (cwd switch)
    Tool: Bash
    Steps: Run `PYTHONPATH=/home/user/PanChongshi/Repo/PanelAgent python -m pytest /home/user/PanChongshi/Repo/PanelAgent/tests/characterization/test_multi_encoding.py /home/user/PanChongshi/Repo/PanelAgent/tests/characterization/test_alias.py -q` with working directory `/tmp`
    Expected: Tests still pass; no file-not-found from relative JSON paths
    Evidence: .sisyphus/evidence/task-6-fixture-alignment-error.txt
  ```

  **Commit**: YES | Message: `test(paths): align fixtures with centralized json settings` | Files: [`tests/conftest.py`, `tests/characterization/*.py`]

- [x] 7. Add cross-flow CWD-independence regression suite

  **What to do**: Add/adjust tests that execute generate/recommend/evaluate flows under changed CWD to guarantee path behavior is stable across runtime entrypoints.
  **Must NOT do**: Must not call real LLM/network services.

  **Recommended Agent Profile**:
  - Category: `unspecified-low` - Reason: integration-oriented regression tests across several flows.
  - Skills: []
  - Omitted: [`ai-sdk`] - not relevant to backend path behavior.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [8] | Blocked By: [1, 3]

  **References**:
  - Pattern: `tests/api/test_recommendations.py:21` - patching LLM for deterministic API tests.
  - Pattern: `tests/api/test_evaluation.py:65` - evaluation flow patch patterns.
  - Pattern: `tests/api/conftest.py:7` - ASGI app client fixture for API path.
  - Test: `tests/test_quality_e2e_integration.py:27` - direct panel-generator flow coverage.

  **Acceptance Criteria**:
  - [ ] Regression suite validates generate/recommend/evaluate behavior with non-root CWD.
  - [ ] All tests are deterministic and isolated via mocks/fixtures.
  - [ ] Evidence includes both passing and intentionally failing edge assertions.

  **QA Scenarios** (MANDATORY):
  ```text
  Scenario: Happy path (cross-flow pass)
    Tool: Bash
    Steps: Run `PYTHONPATH=/home/user/PanChongshi/Repo/PanelAgent python -m pytest /home/user/PanChongshi/Repo/PanelAgent/tests/api/test_panels_generate.py /home/user/PanChongshi/Repo/PanelAgent/tests/api/test_recommendations.py /home/user/PanChongshi/Repo/PanelAgent/tests/api/test_evaluation.py -q` with working directory `/tmp`
    Expected: All selected flow tests pass
    Evidence: .sisyphus/evidence/task-7-crossflow-cwd.txt

  Scenario: Failure/edge case (resolver override to invalid file)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/test_json_path_resolution.py::test_api_flows_invalid_brightness_path_contract -q`
    Expected: Graceful/contracted fallback or explicit expected error per test assertion
    Evidence: .sisyphus/evidence/task-7-crossflow-cwd-error.txt
  ```

  **Commit**: YES | Message: `test(regression): enforce cwd-independent panel flows` | Files: [`tests/api/*.py`, `tests/**`]

- [x] 8. Run final backend verification matrix and collect evidence bundle

  **What to do**: Execute full targeted + backend suite verification and aggregate evidence artifacts for all prior tasks.
  **Must NOT do**: Must not skip failing tests or narrow selectors to hide regressions.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: command execution and evidence collection.
  - Skills: []
  - Omitted: [`frontend-design`] - no frontend scope.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [] | Blocked By: [3, 4, 5, 6, 7]

  **References**:
  - Pattern: `Makefile:6` - backend test command baseline.
  - Pattern: `Makefile:32` - aggregate quality-gate command context.
  - Test: `tests/` - complete backend regression suite.

  **Acceptance Criteria**:
  - [ ] `PYTHONPATH=. python -m pytest tests/ -q` exits 0.
  - [ ] Targeted path-sensitive suites exit 0 from non-root CWD.
  - [ ] Evidence files exist for tasks 1-8 under `.sisyphus/evidence/`.

  **QA Scenarios** (MANDATORY):
  ```text
  Scenario: Happy path (full suite)
    Tool: Bash
    Steps: Run `PYTHONPATH=. python -m pytest tests/ -q`
    Expected: Exit code 0, all tests pass
    Evidence: .sisyphus/evidence/task-8-full-backend-suite.txt

  Scenario: Failure/edge case (strictness check)
    Tool: Bash
    Steps: Run a known-invalid selector to confirm CI captures command failure properly
    Expected: Non-zero exit and clear failure output captured
    Evidence: .sisyphus/evidence/task-8-full-backend-suite-error.txt
  ```

  **Commit**: NO | Message: `n/a` | Files: [`n/a`]

## Final Verification Wave (MANDATORY - after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> Do NOT auto-proceed after verification.
- [x] F1. Plan Compliance Audit - oracle ✅ APPROVE
- [x] F2. Code Quality Review - unspecified-high ✅ APPROVE (5 rounds; all code quality issues fixed. Oracle noted TestProjectRoot tests as "low-value" — subjective, they serve as regression guards for parents[3])
- [x] F3. Real Manual QA - unspecified-high (+ playwright if UI) ⏭️ SKIPPED (backend-only plan, no UI; automated CWD-independence QA completed in T8)
- [x] F4. Scope Fidelity Check - deep ✅ APPROVE (2nd run; .sisyphus/ infra files confirmed as expected)

## Commit Strategy
- Commit 1: `test(paths): add cwd regression for panel brightness loading`
- Commit 2: `refactor(config): add static data path resolver helpers`
- Commit 3: `fix(panel): resolve brightness json via centralized config path`
- Commit 4: `refactor(api): reuse centralized static path resolver`
- Commit 5: `test(regression): enforce cwd-independent panel flows`

## Success Criteria
- The original CWD-dependent path issue in panel generation is removed and guarded by regression tests.
- Static JSON runtime path resolution is centrally managed through `backend/app/core/config.py` logic.
- API and backend tests remain green with no contract drift.
- Scope remains intentionally narrow: no package migration, no JSON file relocation.
