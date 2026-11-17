"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { Me } from "@/types";

const NAV = [
  { href: "/", label: "Overview", min: 1 }, { href: "/users", label: "Users", min: 1 },
  { href: "/conversations", label: "Conversations", min: 2 }, { href: "/compliance", label: "Compliance", min: 2 },
  { href: "/support", label: "Support requests", min: 1 }, { href: "/knowledge", label: "Knowledge base", min: 2 },
  { href: "/settings", label: "Settings", min: 2 },
];
const RANK = { educator: 1, admin: 2, owner: 3 } as const;

export function Sidebar({ me }: { me: Me | null }) {
  const path = usePathname();
  const router = useRouter();
  const rank = me ? RANK[me.role] : 0;
  async function logout() { await fetch("/api/auth/logout", { method: "POST" }); router.push("/login"); }
  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-line bg-navy-950 md:h-screen md:w-60 md:border-b-0 md:border-r">
      <div className="px-5 py-5">
        <div className="text-base font-semibold tracking-tight"><span className="text-teal">Trade</span>Mentor AI</div>
        <div className="text-xs text-ink-dim">Admin console</div>
      </div>
      <nav className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-1 md:flex-col md:overflow-visible">
        {NAV.filter((n) => rank >= n.min).map((n) => {
          const active = n.href === "/" ? path === "/" : path.startsWith(n.href);
          return (
            <Link key={n.href} href={n.href}
                  className={`whitespace-nowrap rounded-md px-3 py-2 text-sm transition-colors ${active ? "bg-navy-700 text-teal" : "text-ink-dim hover:bg-navy-800 hover:text-ink"}`}>
              {n.label}
            </Link>
          );
        })}
      </nav>
      <div className="hidden border-t border-line p-4 text-xs text-ink-dim md:block">
        <div className="truncate">{me?.email}</div>
        <div className="mb-2 capitalize">{me?.role}</div>
        <button onClick={logout} className="btn-ghost w-full">Sign out</button>
      </div>
    </aside>
  );
}
