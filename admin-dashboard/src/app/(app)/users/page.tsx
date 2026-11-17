"use client";
import { useState } from "react";
import { DataTable, fmt } from "@/components/DataTable";
import { PageHeader, State } from "@/components/PageHeader";
import { useApi } from "@/hooks/useApi";
import type { UserRow } from "@/types";

export default function UsersPage() {
  const [q, setQ] = useState("");
  const [applied, setApplied] = useState("");
  const { data, error, loading } = useApi<{ total: number; items: UserRow[] }>(`/users?limit=100${applied ? `&q=${encodeURIComponent(applied)}` : ""}`);
  return (
    <>
      <PageHeader title="Users" sub={data ? `${data.total.toLocaleString()} registered` : undefined}>
        <input className="input w-56" placeholder="Search username or Telegram ID" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && setApplied(q)} />
        <button className="btn-ghost" onClick={() => setApplied(q)}>Search</button>
      </PageHeader>
      <State loading={loading} error={error} empty={!!data && data.items.length === 0} />
      {data && data.items.length > 0 && (
        <DataTable rows={data.items} columns={[
          { header: "Telegram ID", cell: (u) => u.telegram_id },
          { header: "Username", cell: (u) => (u.username ? `@${u.username}` : "–") },
          { header: "Experience", cell: (u) => u.experience?.replace("_", " ") ?? "–" },
          { header: "Registered", cell: (u) => fmt(u.registered_at) },
          { header: "Last activity", cell: (u) => fmt(u.last_active_at) },
        ]} />
      )}
    </>
  );
}
