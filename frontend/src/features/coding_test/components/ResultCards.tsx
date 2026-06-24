import type { SubmissionResult } from "../types";

function Chips({ items, tone }: { items: string[] | null; tone: "good" | "bad" }) {
  if (!items || items.length === 0) {
    return <span className="text-xs text-slate-400">없음</span>;
  }
  const cls =
    tone === "good" ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800";
  return (
    <div className="flex flex-wrap gap-1">
      {items.map((text, i) => (
        <span key={i} className={`rounded-full px-2 py-0.5 text-xs ${cls}`}>
          {text}
        </span>
      ))}
    </div>
  );
}

export function ResultCards({
  result,
  isPending,
}: {
  result?: SubmissionResult;
  isPending: boolean;
}) {
  if (isPending) {
    return (
      <p className="text-sm text-slate-500" role="status">
        채점 중…
      </p>
    );
  }
  if (!result) return null;
  if (result.status === "failed") {
    return (
      <p className="text-sm text-red-700" role="alert">
        채점 실패: {result.error ?? "알 수 없는 오류"}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="rounded border bg-white p-4">
          <p className="text-xs text-slate-500">테스트 점수</p>
          <p className="text-2xl font-bold">
            {result.test_passed}/{result.test_total}
          </p>
        </div>
        <div className="rounded border bg-white p-4">
          <p className="text-xs text-slate-500">코드 품질</p>
          <p className="text-2xl font-bold">{result.code_quality_score ?? "-"}</p>
        </div>
      </div>

      <div className="rounded border bg-white p-4">
        <p className="mb-2 text-sm font-semibold">요약 리포트</p>
        <div className="mb-2">
          <p className="mb-1 text-xs text-slate-500">강점</p>
          <Chips items={result.strengths} tone="good" />
        </div>
        <div>
          <p className="mb-1 text-xs text-slate-500">약점</p>
          <Chips items={result.weaknesses} tone="bad" />
        </div>
      </div>

      <div className="rounded border bg-white p-4">
        <p className="mb-2 text-sm font-semibold">분석 리포트</p>
        <p className="text-sm leading-relaxed">{result.analysis_report}</p>
      </div>
    </div>
  );
}
