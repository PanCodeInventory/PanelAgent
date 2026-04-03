# Deployment Contract

This document captures the exact runtime contract that Docker must preserve for the PanelAgent application. This contract is the foundation for all subsequent Docker work (Dockerfiles, compose, config changes).

---

## 1. Live Service Contract

### Backend
- **URL**: `http://0.0.0.0:8000`
- **Health Endpoint**: `/api/v1/health`
- **Expected Response**: `{"status":"ok","version":"1.0.0"}`
- **CORS Origins** (hardcoded in `backend/app/main.py:37`):
  - `http://localhost:3000`
  - `http://localhost:8501`

### Frontend
- **URL**: `http://0.0.0.0:3000`
- **Runtime Mode**: Next.js dev server (current) / production server (in Docker)
- **API Rewrite**: `/api/v1/*` → `BACKEND_INTERNAL_URL` via Next.js rewrites

---

## 2. Validation Ports (Docker staging only)

| Service  | Host Port | Container Port | Notes |
|----------|-----------|----------------|-------|
| Frontend | 13000     | 3000           | Staging validation port |
| Backend  | 18000     | 8000           | Staging validation port |

**Rule**: Live tmux ports `3000/8000` remain untouched until Docker passes all validation.

---

## 3. Environment File Ownership

### Root `.env`
- **Location**: Project root `.env`
- **Purpose**: Backend configuration
- **Variables**:
  - `OPENAI_API_BASE`
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL_NAME`
- **Loaded by**: `backend/app/core/config.py:15` via pydantic-settings

### `frontend/.env.local`
- **Purpose**: Frontend configuration
- **Variables**:
  - `BACKEND_INTERNAL_URL`
  - `ALLOWED_DEV_ORIGINS`
- **Used at**: Next.js build/runtime

### Docker Rule
- `.env` stays on host
- Injected via `env_file:` in compose
- Never baked into images

---

## 4. Mutable State (must persist across container restarts)

### Quality Registry
- **Root Path**: `data/quality_registry/`
- **Default path from**: `backend/app/services/quality_registry_store.py:95`

#### Directory Structure
```
data/quality_registry/
├── issues.json           # Main record store
├── audit/                # Per-issue append-only audit events
│   ├── f29ec371-91c7-413f-9a8e-30bd521f4ef2.json
│   ├── f0f4dfe6-b6ec-4504-af24-020b67596530.json
│   └── 3b2b2fb6-49a2-4a07-a5f8-b79ac82f5b02.json
└── projections/          # Cached quality projections
    ├── 0c57f1d09e6ec2f2.json
    ├── fc079be6637ea3f7.json
    └── 742f022000ef1c7f.json
```

---

## 5. Static Reference Data (read-only at runtime)

### JSON Configuration Files (project root)
- `channel_mapping.json` — Fluorochrome → system_code mapping
- `fluorochrome_brightness.json` — Brightness ratings 1-5
- `spectral_data.json` — Peak wavelengths, sigma, color

### Inventory CSVs
- **Location**: `inventory/`
- **Files** (5 total):
  1. `panel_inventory.csv`
  2. `impossible_inventory.csv`
  3. `Flourence_List.csv`
  4. `流式抗体库-20250625-人.csv` (Chinese: Flow antibody library - human)
  5. `流式抗体库-20250625小鼠.csv` (Chinese: Flow antibody library - mouse)

**Mount Strategy**: Can be mounted from host or baked into images (read-only).

---

## 6. Python Path Assumptions

### Required Configuration
- **PYTHONPATH**: `.` (project root)
- **Purpose**: Enables `from backend.app...` imports to resolve

### Path Resolution
- `backend/app/core/config.py:54` computes project root as:
  ```python
  Path(__file__).resolve().parents[3]
  ```
- Static data paths resolved relative to project root via `resolve_static_data_path()`

---

## 7. Frontend API Routing

### Next.js Rewrite Configuration
- **File**: `frontend/next.config.ts:25`
- **Rule**: Rewrites `/api/v1/:path*` → `${BACKEND_INTERNAL_URL}/api/v1/:path*`

### API Client
- **File**: `frontend/src/lib/api-client.ts:1`
- **Uses**: `NEXT_PUBLIC_API_URL` or empty string (defaults to rewrite proxy)

### Docker Environment
- **BACKEND_INTERNAL_URL**: `http://backend:8000` (Compose service name)

---

## 8. Container Runtime Mode

### Backend
- **Command**: Production uvicorn (no `--reload`)
- **Bind**: `0.0.0.0:8000`
- **Example**: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`

### Frontend
- **Command**: `next build` + `next start` (NOT `next dev`)
- **Bind**: `0.0.0.0:3000`
- **Process**: Build first, then serve production build

---

## Contract Verification

### Pre-Deployment Checklist
- [ ] Backend health endpoint responds at `http://localhost:8000/api/v1/health`
- [ ] Frontend responds at `http://localhost:3000`
- [ ] Quality registry directory exists with proper structure
- [ ] Static data files present (3 JSON + 5 CSV)
- [ ] Environment files configured correctly

### Post-Docker Validation
- [ ] Staging ports (13000/18000) accessible
- [ ] Health endpoint returns `{"status":"ok","version":"1.0.0"}`
- [ ] Mutable state persists across container restarts
- [ ] API routing works through Next.js proxy

---

*Last updated: 2026-04-03*
*This contract is frozen before any container work begins.*