import { Badge, Chips, Metric, Panel, SectionLabel } from "@/components/ui";

import type { SessionResult } from "../types";
import { ResponseTypeBadge } from "./ResponseTypeBadge";

/** Graded result: overall score + 요약/분석 두 리포트 + per-question breakdown. */
export function ResultView({ result }: { result: SessionResult }) {
  return (
    <div className="space-y-4">
      <header>
        <SectionLabel>CS 심층 평가 결과</SectionLabel>
        <h1 className="mt-1 text-2xl font-bold text-ink-900">채점 리포트</h1>
      </header>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Metric
          label="정규화 점수"
          value={result.normalized_score ?? "—"}
          hint="0~100"
        />
        <Metric
          label="원점수"
          value={result.total_score ?? "—"}
          hint="문항 합(±)"
        />
        <Metric label="문항 수" value={result.per_question.length} />
      </div>

      <Panel>
        <SectionLabel>요약 리포트</SectionLabel>
        <p className="mt-2 text-sm text-ink-900">{result.summary_report}</p>
      </Panel>

      <Panel>
        <SectionLabel>분석 리포트</SectionLabel>
        <p className="mt-2 whitespace-pre-line text-sm text-ink-900">
          {result.analysis_report}
        </p>
      </Panel>

      <div className="space-y-3">
        <SectionLabel>문항별 채점</SectionLabel>
        {result.per_question.map((a) => (
          <Panel key={a.question_id}>
            <div className="flex items-center gap-2">
              <Badge tone="brand">{a.domain}</Badge>
              <ResponseTypeBadge type={a.response_type} />
              <span className="ml-auto font-mono text-sm font-bold tabular-nums text-ink-900">
                {a.score != null ? (a.score > 0 ? `+${a.score}` : a.score) : "—"}
              </span>
            </div>
            {a.rationale ? (
              <p className="mt-2 text-sm text-ink-soft">{a.rationale}</p>
            ) : null}
            {a.matched_keywords && a.matched_keywords.length > 0 ? (
              <div className="mt-2">
                <SectionLabel>짚은 키워드</SectionLabel>
                <Chips items={a.matched_keywords} tone="good" className="mt-1" />
              </div>
            ) : null}
            {a.missing_keywords && a.missing_keywords.length > 0 ? (
              <div className="mt-2">
                <SectionLabel>빠뜨린 키워드</SectionLabel>
                <Chips items={a.missing_keywords} tone="warn" className="mt-1" />
              </div>
            ) : null}
          </Panel>
        ))}
      </div>
    </div>
  );
}
