# Docker LAN Compose Migration Learnings

## T4: Frontend Dockerfile

### Key Findings
- Next.js 16.2.1, no `output: 'standalone'` configured (can't modify next.config.ts)
- Without standalone, runtime image needs full `npm ci --omit=dev` (417MB content size, 2.13GB disk)
- `BACKEND_INTERNAL_URL` is server-side rewrite config → fully runtime configurable
- Alpine package repos unreachable in this environment; used Node.js built-in `fetch` for healthcheck instead of wget
- Docker Hub unreachable directly; used mirror `docker.1ms.run/library/node:20-alpine` then tagged locally
- Adding `frontend/.dockerignore` reduced build context from 1.12GB to ~3KB
- Next.js 16 starts in ~148ms in production mode

### Gotchas
- Docker COPY doesn't support shell redirects (`2>/dev/null`) — use separate RUN or skip
- `npm ci` in deps stage took ~3min; `npm ci --omit=dev` in runner took ~1min
- Healthcheck `wget` requires `apk add` which needs network access to Alpine repos

## T5: Docker Compose

### Key Findings
- `docker compose build --network=host` is NOT supported (unlike `docker build --network=host`)
- Backend pip install succeeded without `--network=host` flag on compose build
- Frontend fully cached on rebuild (all layers from previous T4 build)
- `depends_on: condition: service_healthy` works perfectly — compose waits for backend healthcheck before starting frontend
- Both containers report healthy within ~15 seconds of `up -d`
- Backend healthcheck returns `{"status":"ok","version":"1.0.0"}`
- Frontend healthcheck returns HTTP 200 with Next.js headers
- Compose internal DNS `backend:8000` works for frontend→backend communication
- `env_file: .env` correctly injects OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL_NAME into backend container
- BACKEND_CORS_ORIGINS environment override in compose works for pydantic-settings

### Gotchas
- `--network=host` flag not supported on `docker compose build` subcommand
- Make sure quality_registry volume mount target matches Dockerfile's `RUN mkdir` path (`/app/data/quality_registry`)
