import { adminPath } from "@/lib/admin-path";

const API_BASE = adminPath("/api/v1");

export async function adminFetch<T = unknown>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(
      `Admin API error: ${response.status} ${response.statusText}`,
    );
  }

  return response.json() as Promise<T>;
}

export async function adminPost<T = unknown>(
  path: string,
  body?: unknown,
): Promise<T> {
  return adminFetch<T>(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function adminPut<T = unknown>(
  path: string,
  body?: unknown,
): Promise<T> {
  return adminFetch<T>(path, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function adminDelete<T = unknown>(
  path: string,
): Promise<T> {
  return adminFetch<T>(path, {
    method: "DELETE",
  });
}
