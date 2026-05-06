import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const SESSION_COOKIE_NAME = "panelagent_admin_session";
const ADMIN_PREFIX = process.env.NEXT_PUBLIC_ADMIN_PATH_PREFIX ?? "";
const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

function adminPath(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (!ADMIN_PREFIX) return normalized;
  return ADMIN_PREFIX.endsWith("/")
    ? `${ADMIN_PREFIX}${normalized.slice(1)}`
    : `${ADMIN_PREFIX}${normalized}`;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME);
  const hasSession = !!sessionCookie?.value;

  if (pathname === "/login") {
    if (hasSession) {
      const isValid = await checkSession(sessionCookie!.value);
      if (isValid) {
        return NextResponse.redirect(new URL(adminPath("/settings"), request.url));
      }
      const response = NextResponse.next();
      response.cookies.delete(SESSION_COOKIE_NAME);
      return response;
    }
    return NextResponse.next();
  }

  if (!hasSession) {
    return NextResponse.redirect(new URL(adminPath("/login"), request.url));
  }

  const isValid = await checkSession(sessionCookie!.value);
  if (!isValid) {
    const response = NextResponse.redirect(new URL(adminPath("/login"), request.url));
    response.cookies.delete(SESSION_COOKIE_NAME);
    return response;
  }

  return NextResponse.next();
}

async function checkSession(cookieValue: string): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/admin/auth/session`, {
      headers: { Cookie: `${SESSION_COOKIE_NAME}=${cookieValue}` },
    });
    if (!res.ok) return false;
    const data = await res.json();
    return data.authenticated === true;
  } catch {
    return false;
  }
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api).*)",
  ],
};
