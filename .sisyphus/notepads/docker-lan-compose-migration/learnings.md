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
