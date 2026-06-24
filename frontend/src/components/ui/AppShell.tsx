"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const NAV = [
  { href: "/coding-test", label: "코딩 테스트" },
  { href: "/rejection-eval", label: "거부 능력 평가" },
  { href: "/test-design", label: "테스트 설계 평가" },
  { href: "/dev-prompting", label: "개발 프롬프팅" },
];

/** Light "judge console" top bar + page container used on every route. */
export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  // The entry-code gate (`/`) is a clean full-screen screen — no nav chrome that
  // would let a visitor bypass the gate.
  if (pathname === "/") {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-line bg-surface/90 backdrop-blur">
        <div className="flex h-[52px] w-full items-center gap-4 px-5">
          <Link href="/" className="flex items-center gap-2 font-bold tracking-tight text-ink-900">
            <span className="grid h-6 w-6 place-items-center rounded bg-brand-600 text-xs font-bold text-white">
              &amp;
            </span>
            and·you
          </Link>
          <span className="rounded-sm border border-brand-200 px-2 py-[3px] font-mono text-[11px] tracking-[0.18em] text-brand-600">
            EVAL
          </span>
          <nav className="ml-auto flex items-center gap-1 text-sm text-ink-soft">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-3 py-1.5 hover:bg-paper hover:text-ink-900"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="w-full flex-1 px-6 py-6">{children}</main>
    </div>
  );
}
