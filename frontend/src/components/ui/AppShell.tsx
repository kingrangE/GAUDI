import Link from "next/link";
import type { ReactNode } from "react";

/** Light top bar + page container used on every route. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-[1200px] items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900">
            <span className="grid h-6 w-6 place-items-center rounded-md bg-brand-600 text-xs font-bold text-white">
              &amp;
            </span>
            and you
          </Link>
          <nav className="hidden items-center gap-1 text-sm text-slate-500 sm:flex">
            <Link href="/coding-test" className="rounded-md px-3 py-1.5 hover:bg-slate-100 hover:text-slate-800">
              코딩 테스트
            </Link>
            <Link href="/rejection-eval" className="rounded-md px-3 py-1.5 hover:bg-slate-100 hover:text-slate-800">
              거부 능력 평가
            </Link>
            <Link href="/test-design" className="rounded-md px-3 py-1.5 hover:bg-slate-100 hover:text-slate-800">
              테스트 설계 평가
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1200px] flex-1 px-4 py-6">{children}</main>
    </div>
  );
}
