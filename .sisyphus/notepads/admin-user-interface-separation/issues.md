# Issues — admin-user-interface-separation

(No issues yet — plan execution starting)

## QA Review Findings (2026-04-23)

### Pre-existing test failures (unrelated to separation)
4 tests fail due to localization mismatch - quality context prompts were translated to Chinese but tests still assert English strings:
- `test_panel_evaluate_quality.py::test_quality_context_present_when_projections_exist`
- `test_panel_recommend_quality.py::test_recommend_quality_context_present`
- `test_quality_context_formatter.py::test_header_included_in_context`
- `test_quality_e2e_integration.py::TestEvaluateCandidatesWithLLMContext::test_llm_prompt_contains_quality_context_header`

Root cause: `QUALITY_CONTEXT_HEADER` was localized to `## 抗体质量上下文` but tests check for `## Antibody Quality Context` / `Antibody Quality Notes`.

### Architectural verification: All 10 invariants PASS
- Clean separation between frontend/ and admin-frontend/
- Proxy scoping correct (admin prepends /admin/, user forwards directly)
- Cookie name consistent (`panelagent_admin_session`)
- ADMIN_PASSWORD from env var only

## Scope Fidelity Findings (2026-04-23)

### Guardrail violation: user frontend still references admin API paths
- `grep "/api/v1/admin" frontend/src --include="*.ts" --include="*.tsx"` still matches `frontend/src/lib/api/generated/index.ts`.
- This means the user frontend source tree still carries admin API definitions, so the plan's hard boundary "No user frontend directly calling /api/v1/admin/*" is not fully satisfied under the prescribed check.

### Non-blocking note
- LSP diagnostics are clean for `backend/app` and `backend/app/api/v1/admin`; `frontend/src` only reports TypeScript hints (deprecated `FormEvent`, unused locals), not errors.
