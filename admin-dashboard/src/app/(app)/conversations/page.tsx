"use client";
import Link from "next/link";
import { useState } from "react";
import { Badge } from "@/components/Badge";
import { DataTable, fmt } from "@/components/DataTable";
import { PageHeader, State } from "@/components/PageHeader";
import { useApi } from "@/hooks/useApi";
import type { ConversationRow } from "@/types";

export default function ConversationsPage() {
  const [q, setQ] = useState("");
  const [applied, setApplied] = useState("");
  const { data, error, loading } = useApi<ConversationRow[]>(`/conversations?limit=100${applied ? `&q=${encodeURIComponent(applied)}` : ""}`);
  return (
    <>
      <PageHeader title="Conversations" sub="Search message text across all users">
        <input className="input w-64" placeholder="Search messages" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && setApplied(q)} />
        <button className="btn-ghost" onClick={() => setApplied(q)}>Search</button>
      </PageHeader>
      <State loading={loading} error={error} empty={!!data && data.length === 0} />
      {data && data.length > 0 && (
        <DataTable rows={data} columns={[
          { header: "Conversation", cell: (c) => <Link className="text-teal hover:underline" href={`/conversations/${c.id}`}>#{c.id}</Link> },
          { header: "User", cell: (c) => (c.username ? `@${c.username}` : c.telegram_id) },
          { header: "Messages", cell: (c) => c.messages },
          { header: "Blocked", cell: (c) => (c.blocked ? <Badge tone="red">{c.blocked}</Badge> : "0") },
          { header: "State", cell: (c) => <Badge tone={c.is_active ? "teal" : "gray"}>{c.is_active ? "active" : "reset"}</Badge> },
          { header: "Last message", cell: (c) => fmt(c.last_message_at) },
        ]} />
      )}
    </>
  );
}
