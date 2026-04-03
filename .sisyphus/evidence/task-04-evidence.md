# Task 4: API Endpoints (8 endpoints)
- Files: backend/app/api/v1/endpoints/quality_registry.py (300 lines)
- Tests: tests/api/test_quality_registry.py (26 tests, all pass)
- Endpoints: POST/GET /issues, GET /issues/{id}, GET /issues/{id}/history, POST /candidates/lookup, POST /candidates/confirm, GET /review-queue, POST /review-queue/{id}/resolve
- Verification: PYTHONPATH=. python -m pytest tests/api/test_quality_registry.py -q → 26 passed
