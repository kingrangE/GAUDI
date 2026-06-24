import { Badge } from "@/components/ui/Badge";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";

import type { ResultProblem, ResultResponse } from "../types";

function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

function f1Tone(f1: number): "good" | "warn" | "bad" {
  if (f1 >= 0.8) return "good";
  if (f1 >= 0.5) return "warn";
  return "bad";
}

function ProblemCard({ p }: { p: ResultProblem }) {
  return (
    <Panel className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <SectionLabel>문제 {p.problem_index + 1}</SectionLabel>
          <h3 className="mt-1 text-base font-bold text-ink-900">{p.title}</h3>
        </div>
        <Badge tone={f1Tone(p.f1)}>F1 {pct(p.f1)}</Badge>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <Metric label="Precision" value={pct(p.precision)} />
        <Metric label="Recall" value={pct(p.recall)} />
        <Metric
          label="맞힌 수"
          value={p.correct_count}
          hint={`정답 ${p.truth_count}개 중`}
        />
      </div>
      <p className="text-xs text-ink-soft">
        제출 {p.predicted_ids.length}건 · 정답 {p.truth_count}건 · 누락 {p.fn} · 오탐 {p.fp}
      </p>
    </Panel>
  );
}

/** Final result: overall P/R/F1 + per-problem breakdown (correctness revealed). */
export function ResultSummary({ result }: { result: ResultResponse }) {
  return (
    <div className="space-y-4 py-6">
      <div>
        <p className="text-sm font-semibold text-brand-600">사무직 Prompting</p>
        <h1 className="text-xl font-bold text-ink-900">평가 결과 — {result.candidate_name}</h1>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric label="종합 Precision" value={pct(result.precision)} />
        <Metric label="종합 Recall" value={pct(result.recall)} />
        <Metric label="종합 F1" value={pct(result.f1)} />
        <Metric label="총 맞힌 수" value={result.total_correct} hint="3문제 합계" />
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        {result.problems.map((p) => (
          <ProblemCard key={p.problem_index} p={p} />
        ))}
      </div>
    </div>
  );
}
