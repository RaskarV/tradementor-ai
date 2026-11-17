import type { Overview } from "@/types";

// The product's identity: every draft passes the compliance gate. This strip shows the split.
export function GateStrip({ o }: { o: Overview }) {
  const total = o.messages_processed;
  const blocked = o.messages_blocked;
  const cleared = Math.max(total - blocked, 0);
  const pct = total ? (blocked / total) * 100 : 0;
  return (
    <section className="card p-5">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-sm font-medium">Compliance gate</h2>
        <span className="text-xs text-ink-dim">All outbound messages, all time</span>
      </div>
      <div className="flex items-center gap-3 text-sm">
        <div><div className="text-2xl font-semibold">{total.toLocaleString()}</div><div className="text-xs text-ink-dim">drafts reviewed</div></div>
        <div className="h-px flex-1 bg-gradient-to-r from-sky to-teal" />
        <div className="rounded-md border border-teal/50 px-3 py-2 text-xs text-teal">GATE</div>
        <div className="h-px flex-1 bg-gradient-to-r from-teal to-teal/30" />
        <div className="text-right">
          <div className="text-2xl font-semibold text-teal">{cleared.toLocaleString()}</div><div className="text-xs text-ink-dim">delivered as written</div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-semibold text-alert">{blocked.toLocaleString()}</div><div className="text-xs text-ink-dim">blocked ({pct.toFixed(1)}%)</div>
        </div>
      </div>
      <div className="mt-4 flex h-1.5 overflow-hidden rounded-full bg-navy-700">
        <div className="bg-teal" style={{ width: `${100 - pct}%` }} /><div className="bg-alert" style={{ width: `${pct}%` }} />
      </div>
    </section>
  );
}
