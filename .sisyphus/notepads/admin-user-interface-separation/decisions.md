# Decisions — admin-user-interface-separation

## 2026-04-22 Locked Decisions
- Dual frontend: same repo, two independent Next.js apps (frontend/ + admin-frontend/)
- Same domain, different prefixes: user at /, admin at /admin
- No basePath — reverse-proxy prefix stripping only
- Single-password admin login with session cookie
- Session cookie: panelagent_admin_session, HttpOnly, SameSite=Lax, Secure in prod, TTL=8h
- Password source: env var ADMIN_PASSWORD, compare with hmac.compare_digest
- Admin router: single require_admin_session dependency on entire admin router
- Proxy strategy: route-handler only (remove next.config.ts rewrites)
- Admin browser API path: /admin/api/v1/* → proxied to backend /api/v1/admin/*
- User browser API path: /api/v1/* → proxied to backend /api/v1/*
- Env var: both apps use BACKEND_INTERNAL_URL as sole upstream address
- Admin gate: middleware.ts cookie check + layout session API verification
- Admin login redirect target: /admin/settings
- /admin root redirects to /admin/settings
- History admin endpoint: /api/v1/admin/panel-history/*
- Settings admin endpoint: /api/v1/admin/settings/*
- Quality split: public /api/v1/quality-registry/* (submit only) vs admin /api/v1/admin/quality-registry/* (full mgmt)
- Redirect strategy: 302 initially, documented path to 301 later
- Ports: user frontend 3000, admin frontend 3001, backend 8000, gateway 8080
