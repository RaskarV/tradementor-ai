"use client";
import { Sidebar } from "@/components/Sidebar";
import { useApi } from "@/hooks/useApi";
import type { Me } from "@/types";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { data: me } = useApi<Me>("/auth/me");
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <Sidebar me={me} />
      <main className="min-w-0 flex-1 px-4 py-6 md:px-8">{children}</main>
    </div>
  );
}
