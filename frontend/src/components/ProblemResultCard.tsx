import type { ResultProblem } from "../lib/types";

const pct = (n: number): string => `${Math.round(n * 100)}%`;

export function ProblemResultCard({ problem }: { problem: ResultProblem }) {
  return (
    <div className="panel">
      <div className="spread">
        <h3>{problem.title}</h3>
        <span className="tag">발견율 {pct(problem.recall)}</span>
      </div>
      {problem.report ? <p className="muted">{problem.report}</p> : null}

      <h4>정답 결함</h4>
      <ul>
        {problem.flaws.map((flaw) => (
          <li key={flaw.id} className={flaw.found ? "found" : "missed"}>
            {flaw.found ? "✓" : "✗"} [{flaw.severity}] {flaw.text}
            {flaw.found ? <span className="muted"> (품질 {flaw.quality}/2)</span> : null}
          </li>
        ))}
      </ul>

      {problem.false_positives.length > 0 ? (
        <>
          <h4>허위 지적</h4>
          <ul>
            {problem.false_positives.map((text, i) => (
              <li key={i} className="muted">
                {text}
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}
