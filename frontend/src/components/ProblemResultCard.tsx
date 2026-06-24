import { Badge } from "@/components/ui/Badge";
import { Panel } from "@/components/ui/Panel";
import type { ResultProblem } from "../lib/types";

const pct = (n: number): string => `${Math.round(n * 100)}%`;

function severityTone(severity: string): "bad" | "warn" | "neutral" {
  const s = severity.toLowerCase();
  if (s === "high") return "bad";
  if (s === "medium") return "warn";
  return "neutral";
}

export function ProblemResultCard({ problem }: { problem: ResultProblem }) {
  return (
    <Panel className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-ink-900">{problem.title}</h3>
        <Badge tone={problem.recall >= 0.5 ? "good" : "bad"}>발견율 {pct(problem.recall)}</Badge>
      </div>
      {problem.report ? (
        <p className="rounded-lg bg-paper p-3 text-sm italic text-ink-soft">{problem.report}</p>
      ) : null}

      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">정답 결함</h4>
        <ul className="mt-2 space-y-1.5">
          {problem.flaws.map((flaw) => (
            <li key={flaw.id} className="flex items-start gap-2 text-sm">
              <span className={flaw.found ? "text-good-600" : "text-bad-600"}>
                {flaw.found ? "✓" : "✗"}
              </span>
              <span className="text-ink-soft">
                <Badge tone={severityTone(flaw.severity)} className="mr-1.5 align-middle">
                  {flaw.severity}
                </Badge>
                {flaw.text}
                {flaw.found ? (
                  <span className="text-ink-faint"> (품질 {flaw.quality}/2)</span>
                ) : null}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {problem.false_positives.length > 0 ? (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">허위 지적</h4>
          <ul className="mt-2 space-y-1">
            {problem.false_positives.map((text, i) => (
              <li key={i} className="text-sm text-ink-soft">
                {text}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Panel>
  );
}
