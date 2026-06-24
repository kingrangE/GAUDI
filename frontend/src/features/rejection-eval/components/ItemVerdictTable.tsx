import { Badge } from "@/components/ui/Badge";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";

import type { ResultItem } from "../types";
import { decisionLabel, flawSourceLabel, outcomeMeta, shouldReject } from "../view";

/** Per-item verdict table: 설계 항목 | 내 판정 | 정답 | 상태 (spec-design table analog). */
export function ItemVerdictTable({ items }: { items: ResultItem[] }) {
  return (
    <Panel className="space-y-3">
      <SectionLabel>항목별 판정</SectionLabel>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left font-mono text-[11px] uppercase tracking-[0.1em] text-ink-faint">
            <th className="pb-2 pr-3 font-medium">설계 항목</th>
            <th className="pb-2 pr-3 font-medium">내 판정</th>
            <th className="pb-2 pr-3 font-medium">정답</th>
            <th className="pb-2 font-medium">상태</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const o = outcomeMeta(item.outcome);
            const reject = shouldReject(item.flaw_source);
            return (
              <tr key={item.id} className="border-t border-line align-top">
                <td className="py-2 pr-3 text-ink-900">{item.text}</td>
                <td className="py-2 pr-3 text-ink-soft">{decisionLabel(item.flagged)}</td>
                <td className="py-2 pr-3">
                  {reject ? (
                    <span className="text-ink-soft">
                      거부 대상
                      <span className="block text-xs text-ink-faint">
                        {flawSourceLabel(item.flaw_source)}
                      </span>
                    </span>
                  ) : (
                    <span className="text-ink-soft">수용</span>
                  )}
                </td>
                <td className="py-2">
                  <Badge tone={o.tone}>{o.label}</Badge>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Panel>
  );
}
