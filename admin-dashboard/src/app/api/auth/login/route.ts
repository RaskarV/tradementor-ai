import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const backend = process.env.BACKEND_URL!;
  const body = await req.text();
  const res = await fetch(`${backend}/api/auth/login`, { method: "POST", headers: { "content-type": "application/json" }, body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) return NextResponse.json({ detail: data.detail ?? "Login failed" }, { status: res.status });
  const out = NextResponse.json({ role: data.role, email: data.email });
  out.cookies.set("tm_token", data.token, {
    httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "strict", path: "/", maxAge: 60 * 60 * 8,
  });
  return out;
}
