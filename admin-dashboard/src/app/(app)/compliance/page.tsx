"use client";
import { useState } from "react";
import { Badge, severityTone } from "@/components/Badge";
import { DataTable, fmt } from "@/components/DataTable";
import { PageHeader, State } from "@/components/PageHeader";
import { useApi } from "@/hooks/useApi";
import { api } from "@/services/api";
import type { ComplianceLog, RuleRow } from "@/types";

export default function CompliancePage() {
  const [decision, setDecision] = useState("blocked");
  const logs = useApi<ComplianceLog[]>(`/compliance/logs?limit=100${decision ? `&decision=${decision}` : ""}`);
  const rules = useApi<RuleRow[]>("/compliance/rules");
  const [msg, setMsg] = useState<string | null>(null);
  const [form, setForm] = useState({ code: "", pattern: "", severity: "HIGH" });

  async function act(fn: () => Promise<unknown>) {
    setMsg(null);
    try { await fn(); rules.reload(); } catch (e: any) { setMsg(e.message); }
  }

  return (
    <>
      <PageHeader title="Compliance monitoring" sub="Every outbound message and the gate’s decision">
        <select className="input w-40" value={decision} onChange={(e) => setDecision(e.target.value)}>
          <option value="blocked">Blocked only</option><option value="cleared">Cleared only</option><option value="">All</option>
        </select>
      </PageHeader>
      <State loading={logs.loading} error={logs.error} empty={!!logs.data && logs.data.length === 0} />
      {logs.data && logs.data.length > 0 && (
        <DataTable rows={logs.data} rail={(l) => (l.decision === "blocked" ? "#f87171" : "#2dd4bf")} columns={[
          { header: "Time", cell: (l) => fmt(l.created_at) },
          { header: "Decision", cell: (l) => <Badge tone={l.decision === "blocked" ? "red" : "teal"}>{l.decision}</Badge> },
          { header: "Rules", cell: (l) => <div className="flex flex-wrap gap-1">{l.rules.map((r) => <Badge key={r} tone="amber">{r}</Badge>)}</div> },
          { header: "Severity", cell: (l) => (l.severity ? <Badge tone={severityTone(l.severity)}>{l.severity}</Badge> : "–") },
          { header: "Matched content", cell: (l) => <span className="text-ink-dim">{l.excerpt ?? "–"}</span> },
          { header: "User", cell: (l) => l.user_id ?? "–" },
          { header: "Type", cell: (l) => l.message_type },
        ]} />
      )}

      <h2 className="mb-3 mt-10 text-sm font-medium">Rules</h2>
      {msg && <p className="mb-3 rounded-md border border-alert/40 bg-alert/10 p-3 text-sm text-alert">{msg}</p>}
      {rules.data && (
        <DataTable rows={rules.data} columns={[
          { header: "Rule", cell: (r) => <><div className="font-medium">{r.code}</div><div className="text-xs text-ink-dim">{r.is_builtin ? "built-in" : r.pattern}</div></> },
          { header: "Severity", cell: (r) => (
            <select className="input w-32" value={r.severity} onChange={(e) => act(() => api(`/compliance/rules/${r.code}`, { method: "PUT", json: { severity: e.target.value } }))}>
              {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((s) => <option key={s}>{s}</option>)}
            </select>) },
          { header: "Enabled", cell: (r) => (
            <button className={r.enabled ? "btn-primary" : "btn-ghost"} onClick={() => act(() => api(`/compliance/rules/${r.code}`, { method: "PUT", json: { enabled: !r.enabled } }))}>{r.enabled ? "On" : "Off"}</button>) },
          { header: "", cell: (r) => (!r.is_builtin ? <button className="btn-danger" onClick={() => act(() => api(`/compliance/rules/${r.code}`, { method: "DELETE" }))}>Delete</button> : null) },
        ]} />
      )}
      <div className="card mt-4 grid gap-3 p-4 md:grid-cols-[1fr_2fr_auto_auto]">
        <div><label className="label">Code</label><input className="input" placeholder="NO_CRYPTO" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} /></div>
        <div><label className="label">Regex pattern</label><input className="input" placeholder="\bcrypto\b" value={form.pattern} onChange={(e) => setForm({ ...form, pattern: e.target.value })} /></div>
        <div><label className="label">Severity</label><select className="input" value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>{["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((s) => <option key={s}>{s}</option>)}</select></div>
        <div className="flex items-end"><button className="btn-primary" disabled={!form.code || !form.pattern} onClick={() => act(async () => { await api("/compliance/rules", { method: "POST", json: form }); setForm({ code: "", pattern: "", severity: "HIGH" }); })}>Add rule</button></div>
      </div>
    </>
  );
}
