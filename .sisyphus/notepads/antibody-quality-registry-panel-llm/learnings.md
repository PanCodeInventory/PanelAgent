## [2026-04-02] Session Start
- Plan: antibody-quality-registry-panel-llm
- Session: ses_2b44dafe2ffeyPXlhQCpuGlxy4
- Boulder switched from frontend-backend-agentic-refactor

## [2026-04-02] Task 1: Dual-Key Schema Contracts
- FeedbackKey uses `frozen=True` ConfigDict for automatic hashability; EntityKey overrides `__eq__`/`__hash__` to exclude `lot_number`
- Pyright doesn't recognize frozen Pydantic models as hashable (false positive) — runtime works fine
- Pyright also flags intentionally-invalid construction in ValidationError tests — expected
- Marker normalization: duplicated `_normalize_marker()` in schema module to avoid coupling to `data_preprocessing.py` (which depends on pandas); identical logic
- `model_validator(mode="after")` for blank-string checks on fields that have `min_length=1` (whitespace-only passes Pydantic's length check)
- Pydantic schema style in this project: `str | None = None` (PEP 604), `Field()` for constraints, `default_factory=list` for mutable defaults

## [2026-04-02] Task 2: Registry Persistence Layer
- Used JSON file-based storage: `{data_dir}/issues.json` + `{data_dir}/audit/{issue_id}.json`
- Atomic writes via tempfile + os.replace() prevents corruption
- `get_history()` returns deep copies (`AuditEvent(**e.model_dump())`) to enforce immutability guarantee
- Pydantic `model_dump(mode="json")` serializes nested models (FeedbackKey, EntityKey) correctly for JSON roundtrip
- `FeedbackKey.from_submission()` auto-normalizes marker — no need to normalize before calling
- `tmp_path` pytest fixture gives each test an isolated temp directory — perfect for file-based store tests
- `_update_issue()` helper: find by id in list, merge updates dict, set updated_at, save — avoids code duplication across bind/review/resolve
- ValueError for missing issue_id is sufficient (no custom exception class needed at this layer)

## [2026-04-02] Task 3: Incremental Quality Projection
- Created `ProjectionRecord` model (separate from `AntibodyQualityProjection` schema) to support both bound (entity_key) and unbound (feedback_key) projections without modifying existing schemas
- Storage: `{data_dir}/projections/{sha256_hash[:16]}.json` — one file per unique antibody key
- Key hash uses `entity_key._identity_tuple()` for bound, `(species, marker, fluorochrome, brand, clone)` for unbound
- Binding an issue affects TWO projections: entity_key projection gets the issue, feedback_key projection loses it — `update_projection()` recomputes both
- Dedup: `issue_text.strip().lower()` exact match, keep earliest by `(created_at, issue_id)` tuple comparison
- `latest_issues` = last 5 issues from ascending-sorted deduped list (most recent 5, in chronological order)
- `aggregate_status`: "flagged" if any non-resolved issue exists, "clean" otherwise
- `issue_count` = deduplicated count; `dedup_count` = total - deduplicated
- `get_projections_for_markers()` scans all `*.json` in projections dir, matches on `normalized_marker`, sorts by `issue_count` desc
- Reused `_atomic_write` pattern from store but implemented locally (not importing from store) to keep projection module self-contained
- Projector reads from store but never writes to it — clean read-only dependency

## [2026-04-02] Task 4: Quality Context Formatter
- `format_quality_context()` takes `list[AntibodyQualityProjection]` (NOT `ProjectionRecord`) — the schema-level type, not the internal model
- Deterministic sort: `(-issue_count, normalized_marker)` — most problematic first, alpha tiebreak
- Truncation at line boundary: `rfind("\n")` on budget-trimmed text ensures no partial entries
- Truncation marker appended as a final entry in `entries` list so callers can reconstruct full output from `HEADER + join(entries)`
- `sanitize_for_markdown()`: regex `[#*`]` strip + 200-char limit — simple but sufficient for prompt injection safety
- `get_projections_for_markers()` returns `ProjectionRecord` (internal model) — a conversion step is needed before calling the formatter (future integration task)
- Budget guard: reserve `len(_TRUNCATION_MARKER)` chars before truncation to ensure marker always fits
- LSP shows "Import could not be resolved" for all `backend.*` imports at edit time — this is a false positive; `PYTHONPATH=.` resolves correctly at runtime

## [2026-04-02] Task 5: Quality Registry API Endpoints
- Created `backend/app/api/v1/endpoints/quality_registry.py` with 8 endpoints following the importlib pattern from recommendations.py
- Module-level singletons `_store` and `_projector` — patched via `unittest.mock.patch.object` in tests for isolation with `tmp_path`
- `CandidateConfirmWithIssue(BaseModel)` inline schema avoids modifying existing schema module — combines `issue_id` + `entity_key`
- `ResolveReviewRequest(BaseModel)` inline schema for review resolution — `reviewer` + optional `entity_key`
- Candidate lookup heuristic: load inventory via `data_preprocessing.load_antibody_data()`, filter by normalized marker + fluorochrome, score 1.0 exact / 0.7 partial
- Router prefix `/quality-registry` registered via importlib in `router.py` — same pattern as other modules
- Test fixture `qr_client` creates fresh `QualityRegistryStore` in `tmp_path` and patches module-level singletons — full isolation between tests
- 23 API tests covering all endpoints, validation, error cases, and a full lifecycle integration test
- All existing API tests (39 total) pass with zero regressions

## [2026-04-02] Task 6: Quality Context Injection into evaluate_candidates_with_llm()
- `QUALITY_CONTEXT_HEADER` is defined in `quality_context_formatter.py`, NOT in `quality_registry.py` — easy import mistake
- Module-level singletons `_quality_store` / `_quality_projector` are patchable via `patch("panel_generator._quality_store", ...)` — no need for `patch.object`
- `_build_quality_context_section()` has internal try/except, but `evaluate_candidates_with_llm()` ALSO wraps the call in try/except — defense in depth ensures mocked exceptions don't crash the main flow
- Patching `_build_quality_context_section` with `side_effect=RuntimeError` bypasses the function's internal try/except — the caller's try/except catches it instead
- Quality context is inserted between KEY DIFFERENCES and Evaluation Criteria sections in the prompt — clearly labeled as "Reference ONLY — do NOT auto-exclude"
- `ProjectionRecord` → `AntibodyQualityProjection` conversion filters to `entity_key is not None` only — unbound projections are excluded from prompt context
- Test pattern: set up store + projector in `tmp_path`, patch module singletons, call `evaluate_candidates_with_llm()`, inspect prompt via `mock_llm.call_args[0][0]`
- 5 tests, 150 total pass with zero regressions

## [2026-04-02] Task 8: Frontend API Client + Hooks
- Created `frontend/src/lib/api/quality-registry.ts` with TypeScript interfaces mirroring Pydantic schemas
- Types: FeedbackKey, EntityKey, QualityIssueCreate, QualityIssueResponse, CandidateLookupRequest, CandidateMatch, CandidateLookupResponse, CandidateConfirmRequest, ReviewItemResponse, ResolveReviewRequest, AuditEvent
- API functions use centralized `apiClient` from `@/lib/api-client` — `get<T>(endpoint)` and `post<T>(endpoint, body)` return `Promise<{ data?: T; error?: string }>`
- Created `frontend/src/lib/hooks/use-quality-registry.ts` following hook pattern from existing hooks (usePanelGeneration, useMarkerRecommendation)
- Hook returns: state object + methods (createIssue, listIssues, getIssue, getHistory, lookupCandidates, confirmCandidate, loadReviewQueue, resolveReview, clear, clearError)
- State includes: issues, currentIssue, history, reviewQueue, candidates, isLoading, isLookingUp, isConfirming, error
- All methods use useCallback with empty deps for stable references
- TypeScript check passes with no new errors (`cd frontend && npx tsc --noEmit`)
- Note: No unit test framework installed (no Jest/Vitest), so unit tests not created. Plan mentions Playwright E2E tests for this task.

## [2026-04-02] Task 9: Quality Registry Frontend Page
- Added `frontend/src/components/ui/dialog.tsx` from the shadcn base dialog source after reviewing `npx shadcn@latest docs dialog`; direct CLI install wanted to overwrite existing `button.tsx`, so only the new dialog file was applied.
- Implemented the client-heavy route in `frontend/src/app/quality-registry/quality-registry-client.tsx` and kept `frontend/src/app/quality-registry/page.tsx` as a thin route wrapper because the page exceeded 500 lines.
- Debounced candidate lookup uses marker + fluorochrome + brand after 500ms, opens a controlled dialog with radio selection, and carries the confirmed candidate into submit.
- Backend/API reality check: `confirmCandidate()` requires an existing `issue_id`, so the workable frontend flow is `createIssue()` first and then `confirmCandidate()` for the freshly created issue when a candidate was pre-confirmed in the modal.
- Issue history loads via `listIssues()` on mount, history detail loads via `getHistory(issueId)`, and review queue loads on review-tab activation.
- `cd frontend && npx tsc --noEmit` passes; `npm run build` is blocked by environment because Next.js 16 requires Node >= 20.9.0 while this workspace is on Node 18.19.1.
- TypeScript LSP diagnostics could not run in this environment because `typescript-language-server` is not installed.

## [2026-04-02] Task 10: E2E Integration Tests (Backend + Playwright)
- Created `tests/test_quality_e2e_integration.py` with 4 backend integration tests using real store/projector in tmp_path (no mocks for data layer)
- Created `frontend/e2e/quality-registry.spec.ts` with 3 Playwright E2E tests using route interception for API mocking
- `sanitize_for_markdown()` strips `#` chars from issue text — assertions on LLM prompt must account for this (e.g., "lot #2024-03" becomes "lot 2024-03")
- Playwright route mocking: use `page.route("**/pattern**", handler)` with glob-style URL matching; distinguish GET/POST via `route.request().method()`
- Frontend Tabs component uses `data-state="active"` attribute for active tab detection in Playwright
- Full test suite: 158 backend tests pass, `npx tsc --noEmit` clean

## [2026-04-02] Task 11: Edge Case Tests + Bug Fixes
- Created `tests/test_quality_edge_cases.py` with 41 tests across 15 edge case categories (A-F)
- **Bug fix 1**: `get_projections_for_markers()` had no tiebreak when `issue_count` was equal — fixed to sort by `(-issue_count, normalized_marker)` for deterministic ordering
- **Bug fix 2**: Added `recompute_entity_projection(entity_key)` method to `QualityProjector` for cleaning up stale projections after entity re-binding
- **Bug fix 3**: Updated `candidate_confirm` and `resolve_review` endpoints to call `recompute_entity_projection()` for old entity when rebinding
- `QualityIssueCreate.max_length=2000` rejects text > 2000 chars at Pydantic validation level — 10000-char text test verifies rejection
- `sanitize_for_markdown()` strips `#`, `*`, `` ` `` only; HTML tags like `<script>` and markdown link syntax `[]()` pass through — this is by design (formatting safety, not XSS)
- Empty/whitespace-only `issue_text` is rejected by `model_validator(mode="after")` checking `strip() == ""`, not by `min_length=1` (whitespace has length)
- When formatter truncates, `total_chars` measures the actual truncated output text; the `entries` list only contains complete entries, so `HEADER + join(entries)` may be shorter than `total_chars` — this is expected behavior
- Full test suite: 199 backend tests pass, `npx tsc --noEmit` clean

- 2026-04-02 F2 review: Store/projector/formatter split is clean, and projection output is deterministic via stable sorting plus deduplication.
- 2026-04-02 F2 review: Backend test coverage is broad for persistence/projection/formatter behavior, but gaps remain around invalid entity binding, prompt-injection safety, and frontend interaction state.

## Session: Fix blocking issues F1-F4 (brand filtering + auto-route)

### Key findings
- `_VALID_ISSUE` test constant needed `clone` field added to prevent auto-route breaking 18 existing tests. The auto-route checks `payload.clone` (not `issue.entity_key` which is always None after create).
- Confidence scoring was updated from 0.7 (partial) to a 3-tier system: 1.0 (exact marker+brand), 0.8 (exact marker), 0.5 (partial).
- Brand filter uses case-insensitive substring matching (`brand_filter in row_brand.lower()`).
- The `send_to_review` store method already creates audit events with `actor="system"` — no additional audit logic needed in the endpoint.
