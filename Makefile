.PHONY: test-backend lint-backend lint-frontend typecheck-frontend generate-client check-drift e2e-frontend check-all \
        dev-backend dev-frontend dev-admin-frontend dev-all \
        lint-admin-frontend typecheck-admin-frontend

# ── Backend ──────────────────────────────────────────────────────────────────

test-backend:
	PYTHONPATH=. python -m pytest tests/ -q

lint-backend:
	@command -v ruff >/dev/null 2>&1 && ruff check backend/ || echo "SKIP: ruff not installed — run 'pip install ruff' to enable"

# ── User Frontend ────────────────────────────────────────────────────────────

lint-frontend:
	npm run lint --prefix frontend

typecheck-frontend:
	cd frontend && npx tsc --noEmit

# ── Admin Frontend ───────────────────────────────────────────────────────────

lint-admin-frontend:
	npm run lint --prefix admin-frontend

typecheck-admin-frontend:
	cd admin-frontend && npx tsc --noEmit

# ── Client generation & drift check ─────────────────────────────────────────

generate-client:
	npm run generate:client --prefix frontend

check-drift:
	npm run check:client-drift --prefix frontend

e2e-frontend:
	cd frontend && npx playwright test

# ── Dev servers ──────────────────────────────────────────────────────────────

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

dev-admin-frontend:
	cd admin-frontend && npm run dev -- --port 3001

dev-all:
	@echo "Starting all services (backend + user frontend + admin frontend)..."
	@echo "  Backend:        http://localhost:8000"
	@echo "  User frontend:  http://localhost:3000"
	@echo "  Admin frontend: http://localhost:3001"
	@echo "  Press Ctrl+C to stop all."
	@trap 'kill 0' INT; \
	cd backend && uvicorn app.main:app --reload --port 8000 & \
	cd frontend && npm run dev & \
	cd admin-frontend && npm run dev -- --port 3001 & \
	wait

# ── Aggregate ────────────────────────────────────────────────────────────────

check-all: lint-backend test-backend lint-frontend typecheck-frontend lint-admin-frontend typecheck-admin-frontend generate-client check-drift e2e-frontend
	@echo ""
	@echo "✅ All quality gates passed."
