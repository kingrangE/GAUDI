"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { Logo } from "./Logo";

/** Light "judge console" top bar + page container used on every route. */
export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  // The entry-code gate (`/`) is a clean full-screen screen — no nav chrome that
  // would let a visitor bypass the gate.
  if (pathname === "/") {
    return <>{children}</>;
  }

  // Logo returns to the menu-selection hub (not the entry-code gate, which would
  // force the visitor to re-enter their code). Admin pages return to /admin.
  const homeHref = pathname.startsWith("/admin") ? "/admin" : "/user";

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-line bg-surface/90 backdrop-blur">
        <div className="flex h-[52px] w-full items-center gap-4 px-5">
          <Link href={homeHref} aria-label="GAUDI" className="flex items-center">
            <Logo />
          </Link>
          <span className="rounded-sm border border-brand-200 px-2 py-[3px] font-mono text-[11px] tracking-[0.18em] text-brand-600">
            EVAL
          </span>
        </div>
      </header>
      <main className="w-full flex-1 px-6 py-6">{children}</main>
    </div>
  );
}
