# Learnings — admin-interface-management

## 2026-04-22 Plan Kickoff
- Existing backend: FastAPI + pydantic-settings + lru_cache config, file-based quality_registry_store, stateless panels endpoints
- Existing frontend: Next.js 16 + shadcn/ui, top-level nav in layout.tsx, API wrapper + hook data-layer pattern
- LLM client (llm_api_client.py) initializes OpenAI at module level — must be refactored for per-request runtime config
- OpenAPI client generation workflow: scripts/generate-openapi.py → frontend/scripts/generate-client.mjs → frontend/src/lib/api/generated/index.ts
- Test patterns: pytest (backend API tests under tests/api/), Playwright (frontend e2e), lint/typecheck via Makefile

## 2026-04-22 T1 SQLite Admin Database Layer
- SQLite layer uses `sqlite3` stdlib only, no ORM. WAL journal mode for concurrency safety.
- `init_db()` is idempotent via `CREATE TABLE IF NOT EXISTS` — safe to call from multiple stores.
- `get_connection()` auto-inits if DB missing, returns `sqlite3.Row` factory for dict-like access.
- `llm_settings` table is singleton (id=1 with CHECK constraint) — upsert pattern: check existence, INSERT or UPDATE.
- `panel_history` stores JSON arrays as TEXT for `requested_markers`, `missing_markers`, `selected_panel`.
- Stores accept optional `db_path` for testability — tests use `tmp_path` fixture, never touch real `data/`.
- `project_root()` resolves to repo root via `Path(__file__).resolve().parents[3]` from `backend/app/core/config.py`.
- Default env values: OPENAI_API_BASE="http://127.0.0.1:1234/v1", OPENAI_API_KEY="lm-studio", OPENAI_MODEL_NAME="Qwen3-14B"
