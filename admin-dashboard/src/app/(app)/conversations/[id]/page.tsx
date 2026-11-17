"use client";
import Link from "next/link";
import { Badge } from "@/components/Badge";
import { fmt } from "@/components/DataTable";
import { PageHeader, State } from "@/components/PageHeader";
import { useApi } from "@/hooks/useApi";
import type { ChatMessage } from "@/types";

export default function ConversationDetail({ params }: { params: { id: string } }) {
  const { data, error, loading } = useApi<{ id: number; user_id: number; messages: ChatMessage[] }>(`/conversations/${params.id}`);
  return (
    <>
      <PageHeader title={`Conversation #${params.id}`}><Link href="/conversations" className="btn-ghost">Back</Link></PageHeader>
      <State loading={loading} error={error} />
      <div className="mx-auto max-w-3xl space-y-3">
        {data?.messages.map((m) => (
          <div key={m.id} className={`card p-4 ${m.role === "user" ? "" : "border-l-2 border-l-teal"}`}>
            <div className="mb-2 flex items-center gap-2 text-xs text-ink-dim">
              <span className="font-medium capitalize text-ink">{m.role}</span><span>{fmt(m.created_at)}</span>
              {m.decision && <Badge tone={m.decision === "blocked" ? "red" : "teal"}>{m.decision}</Badge>}
              {m.rules?.map((r) => <Badge key={r} tone="amber">{r}</Badge>)}
            </div>
            <p className="whitespace-pre-wrap text-sm">{m.content}</p>
            {m.original_draft && (
              <details className="mt-3 text-xs text-ink-dim">
                <summary className="cursor-pointer">Blocked draft (never sent)</summary>
                <p className="mt-2 whitespace-pre-wrap rounded bg-alert/10 p-2 text-alert">{m.original_draft}</p>
              </details>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
