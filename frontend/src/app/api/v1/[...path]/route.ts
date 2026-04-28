import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

// LLM calls can take 60+ seconds, so we need a much longer timeout than
// Next.js's default 30s rewrite proxy. This Route Handler forwards every
// request under /api/v1/* to the FastAPI backend with a generous timeout.
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
  const path = pathSegments.join("/");
  const targetUrl = `${BACKEND_URL}/api/v1/${path}${request.nextUrl.search}`;

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
