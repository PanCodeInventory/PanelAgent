# Decisions — admin-interface-management

## 2026-04-22 Planning
- SQLite file: data/admin_console.sqlite3 (two tables: llm_settings, panel_history)
- Settings semantics: global singleton, DB-over-env priority, DB row absent = env-default fallback
- API Key: GET returns has_api_key + api_key_masked only; PUT omit=keep, empty=clear
- History write trigger: only after successful /panels/evaluate with selected_panel
- Quality edit scope: issue_text + reported_by only; identity/status immutable
- History page: read-only, no refill/replay
- No auth, no /admin grouping, no second fetch abstraction
