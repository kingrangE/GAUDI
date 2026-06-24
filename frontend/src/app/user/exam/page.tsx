import Link from "next/link";

export default function ExamPage() {
  return (
    <div className="py-10">
      <div className="mx-auto max-w-2xl rounded-lg border border-line bg-surface p-10 text-center shadow-panel">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-brand-600">실전 모의고사</p>
        <h1 className="mt-3 text-2xl font-bold tracking-tight text-ink-900">준비 중입니다</h1>
        <p className="mt-3 text-ink-soft">
          여러 평가를 묶어 실제 시험처럼 진행하는 실전 모의고사는 곧 제공될 예정입니다.
        </p>
        <Link
          href="/user"
          className="mt-6 inline-flex font-mono text-xs font-semibold uppercase tracking-[0.1em] text-brand-600 hover:text-brand-700"
        >
          ← 돌아가기
        </Link>
      </div>
    </div>
  );
}
