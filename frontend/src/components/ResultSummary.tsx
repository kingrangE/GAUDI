import { Badge } from "@/components/ui/Badge";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import type { ResultResponse } from "../lib/types";

const pct = (n: number): string => `${Math.round(n * 100)}%`;

export function ResultSummary({ result }: { result: ResultResponse }) {
  return (
    <Panel className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-ink-900">{result.candidate_name} 님의 결과</h2>
        <Badge tone="good">{result.status}</Badge>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Metric label="검증 항목 발견율 (Recall)" value={pct(result.recall)} />
        <Metric label="정밀도 (Precision)" value={pct(result.precision)} />
        <Metric label="가중 점수" value={pct(result.weighted_score)} />
      </div>
    </Panel>
  );
}
