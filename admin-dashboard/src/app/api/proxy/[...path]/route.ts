import { NextRequest, NextResponse } from "next/server";

async function handler(req: NextRequest, { params }: { params: { path: string[] } }) {
  const token = req.cookies.get("tm_token")?.value;
  if (!token) return NextResponse.json({ detail: "not authenticated" }, { status: 401 });
  // CSRF defence on top of SameSite=Strict: state-changing calls must carry our custom header.
  if (req.method !== "GET" && req.headers.get("x-requested-with") !== "tm")
    return NextResponse.json({ detail: "forbidden" }, { status: 403 });
  const url = `${process.env.BACKEND_URL}/api/${params.path.join("/")}${req.nextUrl.search}`;
  const headers: Record<string, string> = { authorization: `Bearer ${token}` };
  const ct = req.headers.get("content-type");
  if (ct) headers["content-type"] = ct;
  const hasBody = !["GET", "HEAD"].includes(req.method);
  const res = await fetch(url, { method: req.method, headers, body: hasBody ? await req.arrayBuffer() : undefined, cache: "no-store" });
  return new NextResponse(await res.text(), { status: res.status, headers: { "content-type": res.headers.get("content-type") ?? "application/json" } });
}

export { handler as GET, handler as POST, handler as PUT, handler as PATCH, handler as DELETE };
