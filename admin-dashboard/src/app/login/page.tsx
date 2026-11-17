"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true); setError(null);
    const res = await fetch("/api/auth/login", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email, password }) });
    setBusy(false);
    if (res.ok) { router.push("/"); router.refresh(); return; }
    const d = await res.json().catch(() => ({}));
    setError(typeof d.detail === "string" ? d.detail : "Sign-in failed");
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="card w-full max-w-sm p-7">
        <div className="mb-6 text-lg font-semibold"><span className="text-teal">Trade</span>Mentor AI</div>
        <label className="label" htmlFor="email">Email</label>
        <input id="email" className="input mb-4" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label className="label" htmlFor="pw">Password</label>
        <input id="pw" className="input mb-5" type="password" autoComplete="current-password" value={password}
               onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === "Enter" && submit()} />
        {error && <p className="mb-4 text-sm text-alert">{error}</p>}
        <button className="btn-primary w-full" disabled={busy || !email || !password} onClick={submit}>{busy ? "Signing in…" : "Sign in"}</button>
      </div>
    </main>
  );
}
