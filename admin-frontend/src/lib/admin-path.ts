/**
 * Admin path prefix helper.
 *
 * When behind the nginx gateway (port 8080), all URLs are prefixed with
 * `/admin`. When accessed directly (port 3001), no prefix is used.
 *
 * Set `NEXT_PUBLIC_ADMIN_PATH_PREFIX=/admin` in env for gateway deployments.
 * Leave empty (default) for direct access.
 */

const ADMIN_PREFIX = process.env.NEXT_PUBLIC_ADMIN_PATH_PREFIX ?? "";

export function adminPath(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (!ADMIN_PREFIX) return normalized;
  return ADMIN_PREFIX.endsWith("/")
    ? `${ADMIN_PREFIX}${normalized.slice(1)}`
    : `${ADMIN_PREFIX}${normalized}`;
}
