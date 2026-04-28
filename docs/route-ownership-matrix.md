# Route Ownership Matrix

This document freezes the browser-route, API-route, and legacy-redirect contract for the admin/user split. Later tasks must implement against this matrix and must not change URL decisions ad hoc.

## Locked Decisions

- User pages stay at `/`, `/exp-design`, `/panel-design`, `/quality-registry`.
- Admin pages live at `/admin/login`, `/admin/settings`, `/admin/history`, `/admin/quality-registry`.
- Legacy browser paths `/settings` and `/history` redirect with **302** during migration, then may upgrade to **301** after rollout stabilization.
- `/quality-registry` stays user-facing for issue submission; admin review/editing moves to `/admin/quality-registry`.
- Admin API prefix is `/api/v1/admin/*`.
- Public quality endpoints remain submit-only at `/api/v1/quality-registry/*`.
- Admin quality management moves to `/api/v1/admin/quality-registry/*`.
- Admin settings move to `/api/v1/admin/settings/*`.
- Admin history moves to `/api/v1/admin/panel-history/*`.
- Admin auth endpoints are `/api/v1/admin/auth/login`, `/api/v1/admin/auth/logout`, `/api/v1/admin/auth/session`.

## Browser Page Ownership

| Browser Path | Owner | Notes |
| --- | --- | --- |
| `/` | `user` | User dashboard / landing page remains at the root surface. |
| `/exp-design` | `user` | User experimental design workflow remains unchanged. |
| `/panel-design` | `user` | User panel design workflow remains unchanged. |
| `/quality-registry` | `user` | User-facing quality submission page remains public; no browser redirect. |
| `/settings` | `redirected-to-admin` | Legacy user-surface path; redirect to `/admin/settings` with 302 during migration. |
| `/history` | `redirected-to-admin` | Legacy user-surface path; redirect to `/admin/history` with 302 during migration. |
| `/admin` | `redirected-to-admin` | Admin root is not a destination page; redirect to `/admin/settings`. |
| `/admin/login` | `admin` | Dedicated admin authentication page. |
| `/admin/settings` | `admin` | Canonical admin settings page and default admin landing page. |
| `/admin/history` | `admin` | Canonical admin panel history page. |
| `/admin/quality-registry` | `admin` | Canonical admin quality review/edit/resolve page. |

## API Endpoint Ownership

| API Path | Method | Owner | Migration Notes |
| --- | --- | --- | --- |
| `/api/v1/health` | `GET` | `public-unchanged` | Health check stays public and unchanged. |
| `/api/v1/panels/generate` | `POST` | `public-unchanged` | User panel generation stays under the public API surface. |
| `/api/v1/panels/diagnose` | `POST` | `public-unchanged` | User diagnosis stays under the public API surface. |
| `/api/v1/panels/evaluate` | `POST` | `public-unchanged` | User evaluation stays under the public API surface. |
| `/api/v1/recommendations/markers` | `POST` | `public-unchanged` | User recommendation flow stays public. |
| `/api/v1/spectra/render-data` | `POST` | `public-unchanged` | Spectra rendering stays public. |
| `/api/v1/quality-registry/issues` | `POST` | `public-unchanged` | Public quality submission intake remains at this path. |
| `/api/v1/quality-registry/candidates/lookup` | `POST` | `public-unchanged` | Submission-time candidate lookup remains public. |
| `/api/v1/quality-registry/candidates/confirm` | `POST` | `public-unchanged` | Submission-time candidate confirmation remains public. |
| `/api/v1/quality-registry/issues/{issue_id}` | `PUT` | `admin-migrated` | Editing moves to `PUT /api/v1/admin/quality-registry/issues/{issue_id}`. |
| `/api/v1/quality-registry/issues` | `GET` | `admin-migrated` | Admin listing moves to `GET /api/v1/admin/quality-registry/issues`. |
| `/api/v1/quality-registry/issues/{issue_id}` | `GET` | `admin-migrated` | Admin detail moves to `GET /api/v1/admin/quality-registry/issues/{issue_id}`. |
| `/api/v1/quality-registry/issues/{issue_id}/history` | `GET` | `admin-migrated` | Audit history moves to `GET /api/v1/admin/quality-registry/issues/{issue_id}/history`. |
| `/api/v1/quality-registry/review-queue` | `GET` | `admin-migrated` | Review queue moves to `GET /api/v1/admin/quality-registry/review-queue`. |
| `/api/v1/quality-registry/review-queue/{issue_id}/resolve` | `POST` | `admin-migrated` | Resolve action moves to `POST /api/v1/admin/quality-registry/review-queue/{issue_id}/resolve`. |
| `/api/v1/settings/llm` | `GET` | `admin-migrated` | Settings read moves to `GET /api/v1/admin/settings/llm`. |
| `/api/v1/settings/llm` | `PUT` | `admin-migrated` | Settings write moves to `PUT /api/v1/admin/settings/llm`. |
| `/api/v1/panel-history` | `GET` | `admin-migrated` | History list moves to `GET /api/v1/admin/panel-history`. |
| `/api/v1/panel-history/{entry_id}` | `GET` | `admin-migrated` | History detail moves to `GET /api/v1/admin/panel-history/{entry_id}`. |
| `/api/v1/admin/auth/login` | `POST` | `admin-new` | New admin login endpoint; no public equivalent should remain. |
| `/api/v1/admin/auth/logout` | `POST` | `admin-new` | New admin logout endpoint. |
| `/api/v1/admin/auth/session` | `GET` | `admin-new` | New admin session status endpoint. |

## Legacy Browser Redirect Table

| Old Browser Path | New Browser Path | Redirect Type | Stable Strategy |
| --- | --- | --- | --- |
| `/settings` | `/admin/settings` | `302` | Keep temporary redirect during migration; upgrade to `301` only after admin route is stable in production. |
| `/history` | `/admin/history` | `302` | Keep temporary redirect during migration; upgrade to `301` only after admin route is stable in production. |
| `/admin` | `/admin/settings` | `302` | Keep as canonical admin-root convenience redirect; do not expose a separate `/admin` page. |
