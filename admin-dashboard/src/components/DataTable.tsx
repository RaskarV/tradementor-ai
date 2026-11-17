export interface Column<T> { header: string; cell: (row: T) => React.ReactNode; className?: string }

export function DataTable<T>({ rows, columns, onRowClick, rail }: {
  rows: T[]; columns: Column<T>[]; onRowClick?: (r: T) => void; rail?: (r: T) => string | undefined;
}) {
  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-line text-xs uppercase tracking-wide text-ink-dim">
            {columns.map((c) => <th key={c.header} className={`px-4 py-3 font-medium ${c.className ?? ""}`}>{c.header}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} onClick={onRowClick ? () => onRowClick(r) : undefined}
                className={`border-b border-line/60 last:border-0 ${onRowClick ? "cursor-pointer hover:bg-navy-700/60" : ""}`}>
              {columns.map((c, j) => (
                <td key={c.header} className={`px-4 py-3 align-top ${c.className ?? ""}`}
                    style={j === 0 && rail?.(r) ? { boxShadow: `inset 3px 0 0 ${rail(r)}` } : undefined}>{c.cell(r)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleString() : "–");
