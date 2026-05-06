import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

// Admin proxy: browser calls /api/v1/* are forwarded to backend /api/v1/admin/*
// This ensures the admin frontend cannot accidentally reach public endpoints
// through its own proxy — all traffic is automatically scoped to /admin/.
export const maxDuration = 300; // 5 minutes (Vercel / Next.js upper bound)

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, (await params).path);
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, (await params).path);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, (await params).path);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, (await params).path);
}

async function proxyRequest(request: NextRequest, pathSegments: string[]) {
  const normalizedPathSegments = pathSegments[0] === "admin"
    ? pathSegments.slice(1)
    : pathSegments;
  const path = normalizedPathSegments.join("/");
  // Admin proxy: prepend /admin/ so browser /api/v1/auth/login → backend /api/v1/admin/auth/login
  // Be tolerant of stale clients that already include /admin in the proxied path.
  const targetUrl = `${BACKEND_URL}/api/v1/admin/${path}${request.nextUrl.search}`;

  // Forward all headers except host
  const headers = new Headers(request.headers);
  headers.delete("host");

  let body: BodyInit | null = null;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.arrayBuffer();
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 180_000); // 3 min hard limit

      const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body,
      signal: controller.signal,
      // @ts-expect-error - Next.js fetch supports duplex for streaming request bodies
      duplex: "half",
    });

    clearTimeout(timeout);

    const responseHeaders = new Headers(response.headers);
    // Remove transfer-encoding to avoid issues with Next.js response
    responseHeaders.delete("transfer-encoding");

    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error(`Failed to proxy ${targetUrl}`, error);
    return NextResponse.json(
      { detail: `Proxy error: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 502 },
    );
  }
}
