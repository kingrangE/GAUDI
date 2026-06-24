"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import { getResult } from "@/features/rejection-eval/api";
import { OutcomeBadge } from "@/features/rejection-eval/components/OutcomeBadge";
import type { FlawSource, ResultResponse } from "@/features/rejection-eval/types";

function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

const FLAW_SOURCE_META: Record<
  FlawSource,
  { label: string; tone: "bad" | "warn" } | null
> = {
  injected: { label: "잘못된 설계", tone: "bad" },
  out_of_scope: { label: "요구사항에 없음", tone: "warn" },
  none: null,
};

function FlawSourceBadge({ source }: { source: FlawSource }) {
  const meta = FLAW_SOURCE_META[source];
  if (!meta) return null;
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}

function MetricRow({
  precision,
  recall,
  f1,
}: {
  precision: number;
  recall: number;
  f1: number;
}) {
  return (
    <div className="grid grid-cols-3 gap-3">
      <Metric label="정밀도 (Precision)" value={pct(precision)} />
      <Metric label="재현율 (Recall)" value={pct(recall)} />
      <Metric label="F1" value={pct(f1)} />
    </div>
  );
}

export default function ResultPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getResult(sessionId)
      .then(setResult)
      .catch((e) => setError(e instanceof Error ? e.message : "결과 조회 실패"));
  }, [sessionId]);

  if (error) return <p className="text-bad-600">{error}</p>;
  if (!result) return <p className="text-ink-soft">결과를 불러오는 중…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-900">거부 능력 평가 결과</h1>
        <p className="mt-1 text-ink-soft">
          응시자: <strong className="text-ink-900">{result.candidate_name}</strong>
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-ink-soft">전체 점수</h2>
        <MetricRow precision={result.precision} recall={result.recall} f1={result.f1} />
      </section>

      {result.topics.map((topic) => (
        <Panel key={topic.topic_index} className="space-y-3">
          <h3 className="font-semibold text-ink-900">
            주제 {topic.topic_index + 1}. {topic.topic_title}
          </h3>
          <MetricRow precision={topic.precision} recall={topic.recall} f1={topic.f1} />
          {topic.report ? (
            <p className="rounded-lg bg-paper p-3 text-sm italic text-ink-soft">
              📝 {topic.report}
            </p>
          ) : null}
          <ul className="space-y-3">
            {topic.items.map((item) => (
              <li key={item.id} className="border-t border-line pt-3 first:border-0 first:pt-0">
                <div className="flex flex-wrap items-start gap-2">
                  <OutcomeBadge outcome={item.outcome} />
                  <FlawSourceBadge source={item.flaw_source} />
                  <span className="text-sm text-ink-900">{item.text}</span>
                </div>
                <p className="mt-1 text-xs text-ink-soft">{item.explanation}</p>
              </li>
            ))}
          </ul>
        </Panel>
      ))}
    </div>
  );
}
