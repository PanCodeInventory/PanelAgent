# Task 6: Quality Context → evaluate_candidates_with_llm()
- Files: panel_generator.py (+57 lines quality injection)
- Tests: tests/test_panel_evaluate_quality.py (5 tests, all pass)
- Features: _build_quality_context_section() helper, try/except defense, "Reference ONLY" label
- Verification: PYTHONPATH=. python -m pytest tests/test_panel_evaluate_quality.py -q → 5 passed
