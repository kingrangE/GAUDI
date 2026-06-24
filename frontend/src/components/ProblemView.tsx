import type { ProblemPublic } from "../lib/types";

export function ProblemView({ problem }: { problem: ProblemPublic }) {
  return (
    <div className="panel">
      <h2>{problem.title}</h2>
      <p className="muted">{problem.spec}</p>
      <pre>
        <code>{problem.code}</code>
      </pre>
    </div>
  );
}
