"use client";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { GateStrip } from "@/components/GateStrip";
import { PageHeader, State } from "@/components/PageHeader";
import { useApi } from "@/hooks/useApi";
import type { Overview } from "@/types";

export default function OverviewPage() {
  const { data: o, error, loading, reload } = useApi<Overview>("/overview");
  const stats = o ? [
    ["Registered users", o.total_users], ["Active (7 days)", o.active_users], ["Conversations", o.total_conversations],
    ["Pending support", o.pending_support],
  ] : [];
  return (
    <>
      <PageHeader title="Overview" sub="Activity and compliance at a glance"><button className="btn-ghost" onClick={reload}>Refresh</button></PageHeader>
      <State loading={loading} error={error} />
      {o && (
        <div className="space-y-6">
          <GateStrip o={o} />
          <div className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-line bg-line lg:grid-cols-4">
            {stats.map(([label, v]) => (
              <div key={label as string} className="bg-navy-800 p-5">
                <div className="text-2xl font-semibold">{(v as number).toLocaleString()}</div>
                <div className="mt-1 text-xs text-ink-dim">{label}</div>
              </div>
            ))}
          </div>
          <section className="card p-5">
            <h2 className="mb-4 text-sm font-medium">Messages and blocks, last 14 days</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={o.series} margin={{ left: -16, right: 8, top: 4 }}>
                  <CartesianGrid stroke="#1b2d4d" vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: "#8aa0c0", fontSize: 11 }} tickFormatter={(d: string) => d.slice(5)} axisLine={false} tickLine={false} />
                  <YAxis allowDecimals={false} tick={{ fill: "#8aa0c0", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: "#0f1c33", border: "1px solid #1b2d4d", borderRadius: 8, color: "#e6edf7" }} />
                  <Area type="monotone" dataKey="messages" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} name="Messages" />
                  <Area type="monotone" dataKey="blocked" stroke="#f87171" fill="#f87171" fillOpacity={0.2} name="Blocked" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
      )}
    </>
  );
}
