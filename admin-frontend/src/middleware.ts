import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const SESSION_COOKIE_NAME = "panelagent_admin_session";
const ADMIN_PREFIX = process.env.NEXT_PUBLIC_ADMIN_PATH_PREFIX ?? "";

function adminPath(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (!ADMIN_PREFIX) return normalized;
  return ADMIN_PREFIX.endsWith("/")
    ? `${ADMIN_PREFIX}${normalized.slice(1)}`
    : `${ADMIN_PREFIX}${normalized}`;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME);
  const hasSession = !!sessionCookie?.value;

  if (hasSession && pathname === "/login") {
    return NextResponse.redirect(new URL(adminPath("/settings"), request.url));
  }

  if (!hasSession && pathname !== "/login") {
    return NextResponse.redirect(new URL(adminPath("/login"), request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api).*)",
  ],
};
