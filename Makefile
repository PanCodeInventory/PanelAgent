.PHONY: test-backend lint-backend lint-frontend typecheck-frontend generate-client check-drift e2e-frontend check-all

# ── Backend ──────────────────────────────────────────────────────────────────

test-backend:
	PYTHONPATH=. python -m pytest tests/ -q

lint-backend:
	@command -v ruff >/dev/null 2>&1 && ruff check backend/ || echo "SKIP: ruff not installed — run 'pip install ruff' to enable"

# ── Frontend ─────────────────────────────────────────────────────────────────

lint-frontend:
	npm run lint --prefix frontend

typecheck-frontend:
	cd frontend && npx tsc --noEmit

# ── Client generation & drift check ─────────────────────────────────────────

generate-client:
	npm run generate:client --prefix frontend

check-drift:
	npm run check:client-drift --prefix frontend

e2e-frontend:
	cd frontend && npx playwright test

# ── Aggregate ────────────────────────────────────────────────────────────────

check-all: lint-backend test-backend lint-frontend typecheck-frontend generate-client check-drift e2e-frontend
	@echo ""
	@echo "✅ All quality gates passed."
