const tones: Record<string, string> = {
  teal: "bg-teal/15 text-teal", blue: "bg-sky/15 text-sky", red: "bg-alert/15 text-alert",
  amber: "bg-amber/15 text-amber", gray: "bg-navy-700 text-ink-dim",
};
export function Badge({ children, tone = "gray" }: { children: React.ReactNode; tone?: keyof typeof tones }) {
  return <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}
export const severityTone = (s: string | null) => (s === "CRITICAL" || s === "HIGH" ? "red" : s === "MEDIUM" ? "amber" : "gray");
export const statusTone = (s: string) => (s === "pending" ? "amber" : s === "assigned" ? "blue" : s === "answered" ? "teal" : "gray");
