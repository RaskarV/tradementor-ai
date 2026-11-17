"use client";
import { useRef, useState } from "react";
import { Badge } from "@/components/Badge";
import { DataTable, fmt } from "@/components/DataTable";
import { PageHeader, State } from "@/components/PageHeader";
import { useApi } from "@/hooks/useApi";
import { api } from "@/services/api";
import type { KnowledgeDoc } from "@/types";

const TOPICS = ["market-basics", "nse-bse", "derivatives", "candlesticks", "support-resistance", "indicators", "moving-averages",
  "rsi-macd", "stop-loss", "position-sizing", "risk-reward", "diversification", "psychology", "beginner-mistakes",
  "capital-preservation", "scams"];

export default function KnowledgePage() {
  const docs = useApi<KnowledgeDoc[]>("/knowledge");
  const empty = { id: 0, title: "", topic: TOPICS[0], source_url: "", body: "", is_published: true };
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const file = useRef<HTMLInputElement>(null);

  async function run(fn: () => Promise<unknown>, okText: string) {
    setBusy(true); setMsg(null);
    try { await fn(); setMsg({ ok: true, text: okText }); docs.reload(); }
    catch (e: any) { setMsg({ ok: false, text: e.message }); }
    finally { setBusy(false); }
  }
  async function edit(d: KnowledgeDoc) {
    const full = await api<any>(`/knowledge/${d.id}`);
    setForm({ ...full, source_url: full.source_url ?? "" });
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  }
  const payload = () => ({ title: form.title, topic: form.topic, body: form.body, source_url: form.source_url || null, is_published: form.is_published });

  return (
    <>
      <PageHeader title="Knowledge base" sub="Educational documents the assistant retrieves from">
        <button className="btn-ghost" disabled={busy} onClick={() => run(() => api("/knowledge/rebuild", { method: "POST" }), "Embeddings rebuilt")}>Rebuild embeddings</button>
      </PageHeader>
      {msg && <p className={`mb-4 text-sm ${msg.ok ? "text-teal" : "text-alert"}`}>{msg.text}</p>}
      <State loading={docs.loading} error={docs.error} empty={!!docs.data && docs.data.length === 0} />
      {docs.data && docs.data.length > 0 && (
        <DataTable rows={docs.data} columns={[
          { header: "Title", cell: (d) => <span className="font-medium">{d.title}</span> },
          { header: "Topic", cell: (d) => d.topic },
          { header: "Chunks", cell: (d) => d.chunks },
          { header: "Status", cell: (d) => <Badge tone={d.is_published ? "teal" : "gray"}>{d.is_published ? "published" : "draft"}</Badge> },
          { header: "Updated", cell: (d) => fmt(d.updated_at) },
          { header: "", cell: (d) => (
            <div className="flex gap-2">
              <button className="btn-ghost" onClick={() => edit(d)}>Edit</button>
              <button className="btn-danger" onClick={() => confirm(`Delete “${d.title}”?`) && run(() => api(`/knowledge/${d.id}`, { method: "DELETE" }), "Deleted")}>Delete</button>
            </div>) },
        ]} />
      )}

      <section className="card mt-8 space-y-4 p-5">
        <h2 className="text-sm font-medium">{form.id ? `Edit document #${form.id}` : "Add document"}</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <div><label className="label">Title</label><input className="input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div><label className="label">Topic</label><select className="input" value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })}>{TOPICS.map((t) => <option key={t}>{t}</option>)}</select></div>
          <div><label className="label">Source URL (optional, shown as a citation)</label><input className="input" placeholder="https://…" value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} /></div>
        </div>
        <div><label className="label">Body</label><textarea className="input h-56" value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} /></div>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_published} onChange={(e) => setForm({ ...form, is_published: e.target.checked })} /> Published</label>
        <div className="flex flex-wrap gap-2">
          <button className="btn-primary" disabled={busy || !form.title || form.body.length < 20}
            onClick={() => run(async () => { await (form.id ? api(`/knowledge/${form.id}`, { method: "PUT", json: payload() }) : api("/knowledge", { method: "POST", json: payload() })); setForm(empty); }, "Saved and indexed")}>
            {form.id ? "Save changes" : "Add document"}</button>
          {form.id !== 0 && <button className="btn-ghost" onClick={() => setForm(empty)}>Cancel edit</button>}
          <input ref={file} type="file" accept=".txt,.md" className="hidden" onChange={(e) => {
            const f = e.target.files?.[0]; if (!f) return;
            const fd = new FormData(); fd.append("file", f); fd.append("title", form.title || f.name.replace(/\.\w+$/, "")); fd.append("topic", form.topic);
            if (form.source_url) fd.append("source_url", form.source_url);
            run(() => api("/knowledge/upload", { method: "POST", body: fd }), "Uploaded and indexed"); e.target.value = "";
          }} />
          <button className="btn-ghost" disabled={busy} onClick={() => file.current?.click()}>Upload .txt / .md</button>
        </div>
      </section>
    </>
  );
}
