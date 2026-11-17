"use client";
import { useState } from "react";
import { Badge, statusTone } from "@/components/Badge";
import { DataTable, fmt } from "@/components/DataTable";
import { PageHeader, State } from "@/components/PageHeader";
import { useApi } from "@/hooks/useApi";
import { api } from "@/services/api";
import type { Me, Ticket } from "@/types";

export default function SupportPage() {
  const [status, setStatus] = useState("");
  const list = useApi<Ticket[]>(`/support?limit=100${status ? `&status=${status}` : ""}`);
  const me = useApi<Me>("/auth/me");
  const [openId, setOpenId] = useState<number | null>(null);
  const detail = useApi<Ticket>(openId ? `/support/${openId}` : null);
  const [text, setText] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function act(fn: () => Promise<unknown>, okText: string) {
    setMsg(null);
    try { await fn(); setMsg({ ok: true, text: okText }); list.reload(); detail.reload(); }
    catch (e: any) { setMsg({ ok: false, text: e.message }); }
  }
  const t = detail.data;

  return (
    <>
      <PageHeader title="Support requests" sub="Users who asked for a human educator">
        <select className="input w-40" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>{["pending", "assigned", "answered", "closed"].map((s) => <option key={s}>{s}</option>)}
        </select>
      </PageHeader>
      <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <div>
          <State loading={list.loading} error={list.error} empty={!!list.data && list.data.length === 0} />
          {list.data && list.data.length > 0 && (
            <DataTable rows={list.data} onRowClick={(r) => { setOpenId(r.id); setMsg(null); setText(""); }} columns={[
              { header: "Ticket", cell: (r) => <span className="font-medium">{r.ticket_code}</span> },
              { header: "Status", cell: (r) => <Badge tone={statusTone(r.status)}>{r.status}</Badge> },
              { header: "Assigned", cell: (r) => r.assigned_to ?? "–" },
              { header: "Opened", cell: (r) => fmt(r.created_at) },
            ]} />
          )}
        </div>
        {t && (
          <section className="card space-y-4 p-5">
            <div className="flex items-center justify-between">
              <div><div className="font-semibold">{t.ticket_code}</div><div className="text-xs text-ink-dim">{t.username ? `@${t.username}` : `User ${t.user_id}`}</div></div>
              <Badge tone={statusTone(t.status)}>{t.status}</Badge>
            </div>
            <div>
              <div className="label">Conversation context</div>
              <pre className="max-h-56 overflow-auto whitespace-pre-wrap rounded-md bg-navy-900 p-3 text-xs text-ink-dim">{t.context || "No context stored."}</pre>
            </div>
            {t.status !== "closed" && (
              <>
                <div className="flex flex-wrap gap-2">
                  <button className="btn-ghost" onClick={() => act(() => api(`/support/${t.id}/assign`, { method: "POST", json: {} }), "Assigned to you")}>Assign to me</button>
                  <button className="btn-danger" onClick={() => act(() => api(`/support/${t.id}/status`, { method: "PATCH", json: { status: "closed" } }), "Ticket closed")}>Close ticket</button>
                </div>
                <div>
                  <label className="label">Reply to user (sent via Telegram, checked by the compliance gate)</label>
                  <textarea className="input h-28" value={text} onChange={(e) => setText(e.target.value)} maxLength={3000} />
                  <button className="btn-primary mt-2" disabled={!text.trim()} onClick={() => act(async () => { await api(`/support/${t.id}/reply`, { method: "POST", json: { text } }); setText(""); }, "Reply delivered")}>Send reply</button>
                </div>
              </>
            )}
            {msg && <p className={`text-sm ${msg.ok ? "text-teal" : "text-alert"}`}>{msg.text}</p>}
            {me.data && <p className="text-xs text-ink-dim">Signed in as {me.data.email}</p>}
          </section>
        )}
      </div>
    </>
  );
}
