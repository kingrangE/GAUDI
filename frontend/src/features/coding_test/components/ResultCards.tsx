import { Chips } from "@/components/ui/Chips";
import { Metric } from "@/components/ui/Metric";
import { SectionLabel } from "@/components/ui/SectionLabel";
import type { SubmissionResult } from "../types";

export function ResultCards({
  result,
  isPending,
}: {
  result?: SubmissionResult;
  isPending: boolean;
}) {
  if (isPending) {
    return (
      <p className="text-sm text-ink-soft" role="status">
        채점 중…
      </p>
    );
  }
  if (!result) return null;
  if (result.status === "failed") {
    return (
      <p className="text-sm text-bad-700" role="alert">
        채점 실패: {result.error ?? "알 수 없는 오류"}
      </p>
    );
  }

  const strengths = result.strengths ?? [];
  const weaknesses = result.weaknesses ?? [];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <Metric label="테스트 점수" value={`${result.test_passed}/${result.test_total}`} />
        <Metric label="코드 품질" value={result.code_quality_score ?? "-"} />
      </div>

      <div className="rounded-lg border border-line bg-surface p-4">
        <SectionLabel>요약 리포트</SectionLabel>
        <div className="mt-3 space-y-2">
          <div>
            <p className="mb-1 text-xs text-ink-soft">강점</p>
            {strengths.length > 0 ? (
              <Chips items={strengths} tone="good" />
            ) : (
              <span className="text-xs text-ink-faint">없음</span>
            )}
          </div>
          <div>
            <p className="mb-1 text-xs text-ink-soft">약점</p>
            {weaknesses.length > 0 ? (
              <Chips items={weaknesses} tone="warn" />
            ) : (
              <span className="text-xs text-ink-faint">없음</span>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-line bg-surface p-4">
        <SectionLabel>분석 리포트</SectionLabel>
        <p className="mt-2 text-sm leading-relaxed text-ink-soft">{result.analysis_report}</p>
      </div>
    </div>
  );
}
