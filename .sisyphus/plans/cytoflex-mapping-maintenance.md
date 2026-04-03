# CytoFLEX Mapping Maintenance Document

## TL;DR
> **Summary**: Convert `data/cytoflex_s_fluorochrome_mapping.csv` into a formal maintenance guide without changing runtime behavior. Keep `channel_mapping.json` as runtime source-of-truth.
> **Deliverables**:
> - `data/cytoflex_s_mapping_maintenance.md` (official maintenance doc)
> - Drift/synchronization verification commands documented and executed
> - Evidence artifacts for each task under `.sisyphus/evidence/`
> **Effort**: Short
> **Parallel**: YES - 2 waves
> **Critical Path**: 1 -> 2 -> 3 -> 4 -> 5 -> 6

## Context
### Original Request
User requested: "把 data/cytoflex_s_fluorochrome_mapping.csv 精简成正式维护文档".

### Interview Summary
- CSV currently contains mapping metadata (`fluorochrome`, `canonical_name`, `system_code`, `status`, `notes`) and is suitable as documentation source material.
- Production runtime consumes `channel_mapping.json` (not the CSV) via `data_preprocessing.py`.
- Supporting runtime datasets are `fluorochrome_brightness.json` and `spectral_data.json`.
- User intent is documentation formalization, not runtime remapping.

### Metis Review (gaps addressed)
- Guard against source-of-truth ambiguity: explicitly state JSON remains runtime authority.
- Prevent scope creep into schema/runtime refactor.
- Add executable drift checks between doc and runtime mapping artifacts.
- Add mapping-focused acceptance checks; avoid vague manual criteria.

## Work Objectives
### Core Objective
Create a formal, maintainable, English maintenance document for CytoFLEX mapping that is authoritative for maintenance workflow but non-authoritative for runtime loading.

### Deliverables
- `data/cytoflex_s_mapping_maintenance.md`
- Maintenance sections: scope, authority model, canonical naming rules, `System_Code` catalog, status semantics (`mapped`/`alias`/`unsupported`), change workflow, drift checks, update checklist.
- Evidence files for task execution.

### Definition of Done (verifiable conditions with commands)
- `data/cytoflex_s_mapping_maintenance.md` exists and is non-empty.
- Document contains required authority language:
  - `channel_mapping.json`
  - `runtime source of truth`
  - `update workflow`
  - `synchronization checks`
- Runtime mapping tests still pass:
  - `python -m pytest tests/test_json_path_resolution.py -q`
  - `python -m pytest tests/characterization/test_multi_encoding.py -q`
- Full suite remains green:
  - `python -m pytest tests/ -q`

### Must Have
- Clear authority statement: runtime reads JSON; markdown is maintenance guide.
- Canonical naming and alias policy documented with examples.
- Deterministic update order when changing mappings.
- Drift detection steps executable by agent.

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- Must NOT change runtime loaders or parser logic.
- Must NOT replace `channel_mapping.json` with markdown.
- Must NOT introduce unverified fluorochrome mappings.
- Must NOT include vague instructions like "manual review only".

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after + pytest
- QA policy: Every task includes happy-path and failure/edge scenario
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.md`

## Execution Strategy
### Parallel Execution Waves
Wave 1: authority and structure foundation
- T1 dependency and source-of-truth baseline
- T2 maintenance doc skeleton + authority section

Wave 2: content + governance + validation
- T3 canonical mapping catalog + status semantics
- T4 change workflow + governance rules
- T5 drift checks + executable maintenance checklist
- T6 full verification + evidence package

### Dependency Matrix (full, all tasks)
- T1: Blocks T2-T6 | Blocked By: none
- T2: Blocks T3-T6 | Blocked By: T1
- T3: Blocks T4-T6 | Blocked By: T2
- T4: Blocks T5-T6 | Blocked By: T3
- T5: Blocks T6 | Blocked By: T4
- T6: Final implementation verification | Blocked By: T1-T5

### Agent Dispatch Summary (wave -> task count -> categories)
- Wave 1 -> 2 tasks -> `quick`, `writing`
- Wave 2 -> 4 tasks -> `writing`, `unspecified-low`

## TODOs
> Implementation + Test = ONE task. Never separate.

- [x] 1. Baseline Runtime Authority and Dependencies

  **What to do**: Capture and document where runtime reads mapping data and prove CSV is not runtime-loaded. Record command outputs in evidence.
  **Must NOT do**: Do not modify runtime code or JSON mapping values.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: focused repository inspection
  - Skills: `[]` - no special skill required
  - Omitted: `readme` - avoid broad documentation rewrite behavior

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 2,3,4,5,6 | Blocked By: none

  **References**:
  - Pattern: `backend/app/core/config.py` - static data path authority
  - Pattern: `data_preprocessing.py` - runtime channel mapping load path
  - Pattern: `tests/test_config_static_paths.py` - path resolution contract

  **Acceptance Criteria**:
  - [ ] Evidence captures command outputs proving JSON runtime usage and CSV non-usage.
  - [ ] No non-`.sisyphus/` file is modified in this task.

  **QA Scenarios**:
  ```text
  Scenario: Happy path baseline
    Tool: Bash
    Steps: Run grep/search commands for channel_mapping.json and cytoflex_s_fluorochrome_mapping.csv runtime references
    Expected: JSON has runtime references; CSV has no runtime loader reference
    Evidence: .sisyphus/evidence/task-1-baseline-authority.md

  Scenario: Failure/edge
    Tool: Bash
    Steps: Search for ambiguous phrases implying markdown/runtime authority
    Expected: No existing statement that markdown is runtime source
    Evidence: .sisyphus/evidence/task-1-baseline-authority-error.md
  ```

  **Commit**: NO | Message: `docs(data): baseline cytoflex mapping authority` | Files: `.sisyphus/evidence/*`

- [x] 2. Create Formal Maintenance Document Skeleton

  **What to do**: Create `data/cytoflex_s_mapping_maintenance.md` with fixed sections: Purpose, Runtime Authority, Scope, Data Model, Canonical Naming, System Code Catalog, Status Semantics, Update Workflow, Synchronization Checks, Change Log Template.
  **Must NOT do**: Do not alter any JSON/CSV data in this task.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: precise technical doc structure
  - Skills: `[]`
  - Omitted: `readme` - keep scope narrow to mapping maintenance

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 3,4,5,6 | Blocked By: 1

  **References**:
  - Pattern: `data/cytoflex_s_fluorochrome_mapping.csv` - source columns and status fields
  - Pattern: `channel_mapping.json` - runtime key/value schema

  **Acceptance Criteria**:
  - [ ] New markdown file exists with all required sections.
  - [ ] File explicitly states: `channel_mapping.json` is `runtime source of truth`.

  **QA Scenarios**:
  ```text
  Scenario: Happy path skeleton
    Tool: Read
    Steps: Read the new markdown and verify required headings exist
    Expected: All required sections present and ordered
    Evidence: .sisyphus/evidence/task-2-doc-skeleton.md

  Scenario: Failure/edge
    Tool: Grep
    Steps: Search for forbidden authority claims like "runtime reads this markdown"
    Expected: Zero matches
    Evidence: .sisyphus/evidence/task-2-doc-skeleton-error.md
  ```

  **Commit**: NO | Message: `docs(data): add cytoflex mapping maintenance skeleton` | Files: `data/cytoflex_s_mapping_maintenance.md`

- [x] 3. Populate Canonical Mapping Catalog and Semantics

  **What to do**: Summarize CSV into concise catalog tables in the markdown: system code groups, canonical names, alias examples, unsupported policy. Include explicit examples for `Alexa Fluor 594`, `KIRAVIA Blue 520`, `BV785/BV786`.
  **Must NOT do**: Do not duplicate all 60+ rows verbatim if it harms maintainability; provide maintainable grouped representation.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: structured synthesis from data
  - Skills: `[]`
  - Omitted: `artistry` - avoid stylistic over-optimization

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 4,5,6 | Blocked By: 2

  **References**:
  - Pattern: `data/cytoflex_s_fluorochrome_mapping.csv` - grouped mapping source
  - API/Type: `channel_mapping.json` - runtime format to align terminology

  **Acceptance Criteria**:
  - [ ] Document contains grouped `System_Code` catalog with representative fluorochrome entries.
  - [ ] Alias and unsupported semantics are clearly defined.

  **QA Scenarios**:
  ```text
  Scenario: Happy path catalog coverage
    Tool: Read
    Steps: Verify table sections include all active System_Code families used by runtime mappings
    Expected: Core families (V*, B*, Y*, R*) documented with examples
    Evidence: .sisyphus/evidence/task-3-catalog.md

  Scenario: Failure/edge
    Tool: Grep
    Steps: Search for undefined status tokens beyond mapped/alias/unsupported
    Expected: No undocumented status values
    Evidence: .sisyphus/evidence/task-3-catalog-error.md
  ```

  **Commit**: NO | Message: `docs(data): add canonical mapping catalog` | Files: `data/cytoflex_s_mapping_maintenance.md`

- [x] 4. Define Update Workflow and Governance Rules

  **What to do**: Add deterministic update sequence when adding/changing fluorochromes: update `channel_mapping.json` first (runtime), then support data (`fluorochrome_brightness.json`, `spectral_data.json`), then maintenance markdown and tests.
  **Must NOT do**: Do not prescribe manual-only checks; all steps must be command-verifiable.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: procedural documentation
  - Skills: `[]`
  - Omitted: `git-commit` - commit execution is not part of this task

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 5,6 | Blocked By: 3

  **References**:
  - Pattern: `data_preprocessing.py` - runtime mapping dependency
  - Test: `tests/characterization/test_multi_encoding.py` - mapping behavior verification

  **Acceptance Criteria**:
  - [ ] Workflow includes pre-change, change, and post-change verification commands.
  - [ ] Governance section defines required evidence artifacts for mapping changes.

  **QA Scenarios**:
  ```text
  Scenario: Happy path workflow completeness
    Tool: Read
    Steps: Verify workflow includes ordered steps and explicit command blocks
    Expected: No missing stage in lifecycle (pre/change/post)
    Evidence: .sisyphus/evidence/task-4-workflow.md

  Scenario: Failure/edge
    Tool: Grep
    Steps: Search for ambiguous wording like "update as needed"
    Expected: No ambiguous workflow language
    Evidence: .sisyphus/evidence/task-4-workflow-error.md
  ```

  **Commit**: NO | Message: `docs(data): define mapping governance workflow` | Files: `data/cytoflex_s_mapping_maintenance.md`

- [x] 5. Add Synchronization Checks and Drift Detection

  **What to do**: Add executable drift checks in markdown to detect mismatch between maintenance document statements and runtime JSON keys/examples.
  **Must NOT do**: Do not require human spreadsheet comparisons.

  **Recommended Agent Profile**:
  - Category: `unspecified-low` - Reason: lightweight command/spec section
  - Skills: `[]`
  - Omitted: `deep` - not needed for simple drift command definitions

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 6 | Blocked By: 4

  **References**:
  - Pattern: `tests/test_json_path_resolution.py` - path/regression safety expectation
  - API/Type: `backend/app/core/config.py` - canonical file path naming

  **Acceptance Criteria**:
  - [ ] Document includes at least two executable drift-check commands with expected outcomes.
  - [ ] Commands reference real repository paths.

  **QA Scenarios**:
  ```text
  Scenario: Happy path drift check
    Tool: Bash
    Steps: Execute documented drift command(s)
    Expected: Command exits 0 and reports no critical drift
    Evidence: .sisyphus/evidence/task-5-drift.md

  Scenario: Failure/edge
    Tool: Bash
    Steps: Simulate mismatch condition in command input pattern (without file mutation)
    Expected: Command surfaces mismatch signal path
    Evidence: .sisyphus/evidence/task-5-drift-error.md
  ```

  **Commit**: NO | Message: `docs(data): add sync and drift checks` | Files: `data/cytoflex_s_mapping_maintenance.md`

- [x] 6. Final Verification and Evidence Consolidation

  **What to do**: Run required tests/greps, collect outputs, and ensure the maintenance doc is complete and runtime-safe.
  **Must NOT do**: Do not modify runtime data files in this step.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: verification pass
  - Skills: `[]`
  - Omitted: `writing` - no content authoring expected

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: none | Blocked By: 1,2,3,4,5

  **References**:
  - Test: `tests/test_json_path_resolution.py`
  - Test: `tests/characterization/test_multi_encoding.py`
  - Test: `tests/`

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/test_json_path_resolution.py -q` passes.
  - [ ] `python -m pytest tests/characterization/test_multi_encoding.py -q` passes.
  - [ ] `python -m pytest tests/ -q` passes.
  - [ ] Required authority/workflow/sync keywords are present in doc.

  **QA Scenarios**:
  ```text
  Scenario: Happy path final verification
    Tool: Bash
    Steps: Run all required pytest and keyword grep checks
    Expected: All commands exit 0
    Evidence: .sisyphus/evidence/task-6-final-verify.md

  Scenario: Failure/edge
    Tool: Grep
    Steps: Verify forbidden claims (markdown runtime authority) are absent
    Expected: Zero forbidden matches
    Evidence: .sisyphus/evidence/task-6-final-verify-error.md
  ```

  **Commit**: YES | Message: `docs(data): add cytoflex mapping maintenance guide` | Files: `data/cytoflex_s_mapping_maintenance.md`

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> Do NOT auto-proceed after verification.
- [x] F1. Plan Compliance Audit - oracle
- [x] F2. Code Quality Review - unspecified-high
- [x] F3. Real Manual QA - unspecified-high (+ playwright if UI)
- [x] F4. Scope Fidelity Check - deep

## Commit Strategy
- Single implementation commit preferred:
  - `docs(data): add cytoflex mapping maintenance guide`
- Optional split (if needed for review clarity):
  1) `docs(plan): define cytoflex mapping maintenance workflow`
  2) `docs(data): publish cytoflex mapping maintenance guide`

## Success Criteria
- Formal maintenance doc exists and is discoverable near mapping artifacts.
- Runtime authority model is explicit and unambiguous.
- Drift checks and update workflow are executable and evidence-backed.
- All required tests pass with no runtime behavior regressions.
