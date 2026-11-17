export function PageHeader({ title, sub, children }: { title: string; sub?: string; children?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {sub && <p className="mt-1 text-sm text-ink-dim">{sub}</p>}
      </div>
      <div className="flex items-center gap-2">{children}</div>
    </div>
  );
}
export function State({ loading, error, empty }: { loading: boolean; error: string | null; empty?: boolean }) {
  if (loading) return <p className="py-6 text-sm text-ink-dim">Loading…</p>;
  if (error) return <p className="rounded-md border border-alert/40 bg-alert/10 p-3 text-sm text-alert">{error}</p>;
  if (empty) return <p className="py-6 text-sm text-ink-dim">Nothing to show yet.</p>;
  return null;
}
