# PARITY GATE — Streamlit Decommission Readiness

> **Streamlit retirement should ONLY proceed after ALL items below are checked.**

---

## 1. Backend API Parity

Every Streamlit function must be wrapped by a backend API endpoint.

| # | Check | Verification | Status |
|---|-------|-------------|--------|
| 1.1 | `recommend_markers_from_inventory()` → `POST /api/v1/recommendations/markers` | `PYTHONPATH=. python -m pytest tests/api/test_recommendations.py -q` | ☐ |
| 1.2 | `generate_candidate_panels()` → `POST /api/v1/panels/generate` | `PYTHONPATH=. python -m pytest tests/api/test_panels.py -q` | ☐ |
| 1.3 | `diagnose_conflicts()` → `POST /api/v1/panels/diagnose` | `PYTHONPATH=. python -m pytest tests/api/test_panels.py::test_diagnose -q` | ☐ |
| 1.4 | `evaluate_candidates_with_llm()` → `POST /api/v1/panels/evaluate` | `PYTHONPATH=. python -m pytest tests/api/test_panels.py::test_evaluate -q` | ☐ |
| 1.5 | `plot_panel_spectra()` / `get_gaussian_curve()` → `POST /api/v1/spectra/render-data` | `PYTHONPATH=. python -m pytest tests/api/test_spectra.py -q` | ☐ |
| 1.6 | CORS configured for frontend origin | `grep -q 'allow_origins' backend/app/main.py` | ☐ |

---

## 2. Frontend UI Parity

Every Streamlit tab/page must be reproduced in the Next.js frontend.

| # | Check | Verification | Status |
|---|-------|-------------|--------|
| 2.1 | Tab 1 — Experimental Design → `/exp-design` | `test -f frontend/src/app/exp-design/page.tsx` | ☐ |
| 2.2 | Tab 2 — Panel Generation → `/panel-design` | `test -f frontend/src/app/panel-design/page.tsx` | ☐ |
| 2.3 | Marker recommendation flow (goal → AI → table) | Manual: navigate to `/exp-design`, fill goal, click Recommend | ☐ |
| 2.4 | Panel search flow (markers → candidates → tabs) | Manual: navigate to `/panel-design`, enter markers, click Search | ☐ |
| 2.5 | AI evaluation of candidates | Manual: select candidates, click Evaluate with AI | ☐ |
| 2.6 | Spectral visualization (Gaussian curves) | Manual: select candidate, verify spectra chart renders | ☐ |
| 2.7 | Conflict diagnosis display | Manual: enter conflicting markers, verify diagnosis shown | ☐ |
| 2.8 | Exp Design → Panel Design cross-navigation (markers passed via URL) | Manual: click "Use This Panel" on exp-design, verify pre-fill | ☐ |

---

## 3. Data Flow Parity

Same inputs must produce the same outputs in Streamlit and the new stack.

| # | Check | Verification | Status |
|---|-------|-------------|--------|
| 3.1 | Marker normalization matches (`normalize_marker_name`) | Compare API output vs Streamlit for identical marker list | ☐ |
| 3.2 | Panel generation produces identical candidates | Compare API `/api/v1/panels/generate` output vs Streamlit solver | ☐ |
| 3.3 | Spectral data matches (same Gaussian parameters) | Compare API `/api/v1/spectra/render-data` vs Streamlit `plot_panel_spectra` | ☐ |
| 3.4 | Conflict diagnosis messages match | Compare API `/api/v1/panels/diagnose` output vs Streamlit display | ☐ |
| 3.5 | LLM evaluation uses same prompt template | Compare `panel_generator.py` prompt vs API wrapper behavior | ☐ |
| 3.6 | Species selection and inventory loading identical | Verify both stacks load same CSV files via `INVENTORY_CONFIG` | ☐ |

---

## 4. Quality Gates

All CI checks must be green.

| # | Check | Command | Status |
|---|-------|---------|--------|
| 4.1 | Backend tests pass | `PYTHONPATH=. python -m pytest tests/ -q` | ☐ |
| 4.2 | Frontend lint passes | `npm run lint --prefix frontend` | ☐ |
| 4.3 | Frontend typecheck passes | `cd frontend && npx tsc --noEmit` | ☐ |
| 4.4 | Client generation succeeds | `npm run generate:client --prefix frontend` | ☐ |
| 4.5 | Client drift check clean | `npm run check:client-drift --prefix frontend` | ☐ |
| 4.6 | Full `make check-all` passes | `make check-all` | ☐ |
| 4.7 | GitHub Actions CI green | Check Actions tab on latest commit to main | ☐ |

---

## Sign-Off

| Role | Name | Date |
|------|------|------|
| Backend lead | | |
| Frontend lead | | |
| QA / Integration | | |

**Streamlit decommission date:** _______________
