// All calls go through the Next.js proxy, which attaches the admin token from an httpOnly cookie.
export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T = unknown>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("x-requested-with", "tm");
  let body = init.body;
  if (init.json !== undefined) { headers.set("content-type", "application/json"); body = JSON.stringify(init.json); }
  const res = await fetch(`/api/proxy${path}`, { ...init, headers, body, cache: "no-store" });
  if (res.status === 401 && typeof window !== "undefined" && !location.pathname.startsWith("/login")) {
    location.href = "/login";
  }
  const text = await res.text();
  let data: any = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const d = data?.detail;
    throw new ApiError(res.status, typeof d === "string" ? d : d?.error ?? `Request failed (${res.status})`);
  }
  return data as T;
}
