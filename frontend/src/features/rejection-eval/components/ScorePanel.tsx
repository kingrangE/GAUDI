import { Badge } from "@/components/ui/Badge";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";

import type { ResultTopic } from "../types";
import { percent, verdictMeta } from "../view";

const TONE_TEXT: Record<string, string> = {
  good: "text-good-600",
  warn: "text-warn-600",
  bad: "text-bad-600",
  neutral: "text-ink-900",
};

/** Headline score card: big F1 with verdict tone + Precision/Recall + report. */
export function ScorePanel({ topic }: { topic: ResultTopic }) {
  const v = verdictMeta(topic.f1);
  return (
    <Panel className="space-y-4">
      <SectionLabel>거부 능력 점수</SectionLabel>
      <div className="flex items-end gap-3">
        <span
          className={`font-mono text-5xl font-bold tabular-nums ${TONE_TEXT[v.tone]}`}
        >
          {Math.round(topic.f1 * 100)}
        </span>
        <span className="pb-1 text-ink-faint">/ 100</span>
        <span className="pb-1.5">
          <Badge tone={v.tone}>{v.label}</Badge>
        </span>
      </div>
      {topic.report ? <p className="text-sm text-ink-soft">{topic.report}</p> : null}
      <div className="grid grid-cols-3 gap-3">
        <Metric label="F1" value={percent(topic.f1)} />
        <Metric label="정밀도 (Precision)" value={percent(topic.precision)} />
        <Metric label="재현율 (Recall)" value={percent(topic.recall)} />
      </div>
    </Panel>
  );
}
