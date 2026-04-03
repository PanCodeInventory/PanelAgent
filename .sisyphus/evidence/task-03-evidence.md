# Task 3: Save-Time Incremental Projection
- Files: backend/app/services/quality_projection.py (284 lines)
- Tests: tests/test_quality_projection.py (15 tests, all pass)
- Features: antibody-level aggregation, dedup by issue_text.strip().lower(), deterministic ordering
- Verification: PYTHONPATH=. python -m pytest tests/test_quality_projection.py -q → 15 passed
