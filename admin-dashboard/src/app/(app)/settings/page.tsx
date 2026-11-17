"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/Badge";
import { DataTable } from "@/components/DataTable";
import { PageHeader, State } from "@/components/PageHeader";
import { useApi } from "@/hooks/useApi";
import { api } from "@/services/api";
import type { AdminRow, Me } from "@/types";

interface Settings {
  system_prompt_extra: string; llm: { provider: string | null; model: string | null };
  notifications: Record<string, boolean>; compliance: { block_threshold: string; regulatory_phrases: string[] };
  risk_limits: Record<string, string>;
}

export default function SettingsPage() {
  const { data, error, loading, reload } = useApi<Settings>("/settings");
  const me = useApi<Me>("/auth/me");
  const isOwner = me.data?.role === "owner";
  const admins = useApi<AdminRow[]>(isOwner ? "/admins" : null);
  const [s, setS] = useState<Settings | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [phrases, setPhrases] = useState("");
  const [na, setNa] = useState({ email: "", password: "", role: "educator", telegram_id: "" });
  useEffect(() => { if (data) { setS(data); setPhrases(data.compliance.regulatory_phrases.join("\n")); } }, [data]);

  async function save(key: string, value: unknown) {
    setMsg(null);
    try { await api(`/settings/${key}`, { method: "PUT", json: { value } }); setMsg({ ok: true, text: `Saved ${key}` }); reload(); }
    catch (e: any) { setMsg({ ok: false, text: e.message }); }
  }
  async function adminAct(fn: () => Promise<unknown>) {
    setMsg(null);
    try { await fn(); admins.reload(); } catch (e: any) { setMsg({ ok: false, text: e.message }); }
  }

  return (
    <>
      <PageHeader title="Settings" sub="Changes apply within about 30 seconds and are written to the audit log" />
      <State loading={loading} error={error} />
      {msg && <p className={`mb-4 text-sm ${msg.ok ? "text-teal" : "text-alert"}`}>{msg.text}</p>}
      {s && (
        <div className="max-w-3xl space-y-6">
          <section className="card space-y-3 p-5">
            <h2 className="text-sm font-medium">AI provider</h2>
            <div className="grid gap-3 md:grid-cols-2">
              <div><label className="label">Provider</label>
                <select className="input" value={s.llm.provider ?? ""} onChange={(e) => setS({ ...s, llm: { ...s.llm, provider: e.target.value || null } })}>
                  <option value="">Environment default</option><option value="claude">Claude</option><option value="openai">OpenAI</option></select></div>
              <div><label className="label">Model override (optional)</label><input className="input" value={s.llm.model ?? ""} onChange={(e) => setS({ ...s, llm: { ...s.llm, model: e.target.value || null } })} /></div>
            </div>
            <button className="btn-primary" onClick={() => save("llm", s.llm)}>Save provider</button>
          </section>

          <section className="card space-y-3 p-5">
            <h2 className="text-sm font-medium">System prompt guidance</h2>
            <p className="text-xs text-ink-dim">Appended to the built-in prompt. It cannot override the safety rules, which live in code, and the compliance gate checks every reply regardless.</p>
            <textarea className="input h-32" maxLength={2000} value={s.system_prompt_extra} onChange={(e) => setS({ ...s, system_prompt_extra: e.target.value })} />
            <button className="btn-primary" onClick={() => save("system_prompt_extra", s.system_prompt_extra)}>Save guidance</button>
          </section>

          <section className="card space-y-3 p-5">
            <h2 className="text-sm font-medium">Compliance policy</h2>
            <div><label className="label">Block threshold</label>
              <select className="input w-48" value={s.compliance.block_threshold} onChange={(e) => setS({ ...s, compliance: { ...s.compliance, block_threshold: e.target.value } })}>
                {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((x) => <option key={x}>{x}</option>)}</select>
              <p className="mt-1 text-xs text-ink-dim">Matches at or above this severity block the message. Raising it above MEDIUM requires an owner.</p></div>
            <div><label className="label">Regulatory restriction phrases (one per line)</label><textarea className="input h-24" value={phrases} onChange={(e) => setPhrases(e.target.value)} /></div>
            <button className="btn-primary" onClick={() => save("compliance", { block_threshold: s.compliance.block_threshold, regulatory_phrases: phrases.split("\n").map((x) => x.trim()).filter(Boolean) })}>Save policy</button>
          </section>

          <section className="card space-y-3 p-5">
            <h2 className="text-sm font-medium">Administrator notifications (Telegram)</h2>
            {Object.keys(s.notifications).map((k) => (
              <label key={k} className="flex items-center gap-2 text-sm capitalize"><input type="checkbox" checked={s.notifications[k]} onChange={(e) => setS({ ...s, notifications: { ...s.notifications, [k]: e.target.checked } })} />{k.replace("_", " ")}</label>
            ))}
            <button className="btn-primary" onClick={() => save("notifications", s.notifications)}>Save notifications</button>
          </section>

          <section className="card space-y-3 p-5">
            <h2 className="text-sm font-medium">Risk calculator limits</h2>
            <div className="grid gap-3 md:grid-cols-4">
              {Object.keys(s.risk_limits).map((k) => (
                <div key={k}><label className="label">{k.replace(/_/g, " ")}</label><input className="input" value={s.risk_limits[k]} onChange={(e) => setS({ ...s, risk_limits: { ...s.risk_limits, [k]: e.target.value } })} /></div>
              ))}
            </div>
            <button className="btn-primary" onClick={() => save("risk_limits", s.risk_limits)}>Save limits</button>
          </section>

          {isOwner && admins.data && (
            <section className="space-y-3">
              <h2 className="text-sm font-medium">Administrator access</h2>
              <DataTable rows={admins.data} columns={[
                { header: "Email", cell: (a) => a.email }, { header: "Role", cell: (a) => <Badge tone="blue">{a.role}</Badge> },
                { header: "Telegram ID", cell: (a) => a.telegram_id ?? "–" },
                { header: "Active", cell: (a) => (
                  <button className={a.is_active ? "btn-primary" : "btn-ghost"} onClick={() => adminAct(() => api(`/admins/${a.id}`, { method: "PATCH", json: { is_active: !a.is_active } }))}>{a.is_active ? "Active" : "Disabled"}</button>) },
                { header: "Change role", cell: (a) => (
                  <select className="input w-32" value={a.role} onChange={(e) => adminAct(() => api(`/admins/${a.id}`, { method: "PATCH", json: { role: e.target.value } }))}>
                    {["educator", "admin", "owner"].map((r) => <option key={r}>{r}</option>)}</select>) },
              ]} />
              <div className="card grid gap-3 p-4 md:grid-cols-5">
                <input className="input md:col-span-2" placeholder="email" value={na.email} onChange={(e) => setNa({ ...na, email: e.target.value })} />
                <input className="input" type="password" placeholder="password (12+ chars)" value={na.password} onChange={(e) => setNa({ ...na, password: e.target.value })} />
                <select className="input" value={na.role} onChange={(e) => setNa({ ...na, role: e.target.value })}>{["educator", "admin", "owner"].map((r) => <option key={r}>{r}</option>)}</select>
                <input className="input" placeholder="Telegram ID (optional)" value={na.telegram_id} onChange={(e) => setNa({ ...na, telegram_id: e.target.value })} />
                <button className="btn-primary md:col-span-5" disabled={!na.email || na.password.length < 12}
                  onClick={() => adminAct(async () => { await api("/admins", { method: "POST", json: { ...na, telegram_id: na.telegram_id ? Number(na.telegram_id) : null } }); setNa({ email: "", password: "", role: "educator", telegram_id: "" }); })}>Add administrator</button>
              </div>
            </section>
          )}
        </div>
      )}
    </>
  );
}
