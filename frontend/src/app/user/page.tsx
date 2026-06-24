import Link from "next/link";

const ENTRIES = [
  {
    href: "/user/practice",
    badge: "개별 연습",
    title: "개별 연습",
    desc: "여러 평가를 항목별로 자유롭게 연습합니다. 원하는 평가를 골라 바로 시작하세요.",
    cta: "연습 시작 →",
    ready: true,
  },
  {
    href: "/user/exam",
    badge: "실전 모의고사",
    title: "실전 모의고사",
    desc: "5개 평가를 하나의 실제 과제처럼 순서대로 진행합니다. 점수는 종료 후 관리자가 확인합니다.",
    cta: "시험 시작 →",
    ready: true,
  },
];

export default function UserHubPage() {
  return (
    <div className="py-10">
      <section>
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-brand-600">and·you · 응시자</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-ink-900">무엇을 진행할까요?</h1>
        <p className="mt-3 max-w-3xl text-ink-soft">
          개별 연습으로 항목을 익히거나, 실전 모의고사로 실제 시험을 대비하세요.
        </p>
      </section>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {ENTRIES.map((e) => (
          <Link
            key={e.href}
            href={e.href}
            aria-disabled={!e.ready}
            className="group flex min-h-[200px] flex-col rounded-lg border border-line bg-surface p-6 shadow-panel transition-colors hover:border-brand-300"
          >
            <span className="inline-flex w-fit rounded-sm border border-brand-200 px-2 py-[3px] font-mono text-[11px] uppercase tracking-[0.12em] text-brand-600">
              {e.badge}
            </span>
            <h2 className="mt-4 text-2xl font-semibold text-ink-900">{e.title}</h2>
            <p className="mt-2 flex-1 text-sm text-ink-soft">{e.desc}</p>
            <span
              className={
                e.ready
                  ? "mt-4 font-mono text-xs font-semibold uppercase tracking-[0.1em] text-brand-600 group-hover:text-brand-700"
                  : "mt-4 font-mono text-xs font-semibold uppercase tracking-[0.1em] text-ink-faint"
              }
            >
              {e.cta}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
