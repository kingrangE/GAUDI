import type { ProblemPublic } from "../lib/types";

/** Left-column problem brief: title + spec. The code lives in a dark CodePanel. */
export function ProblemView({ problem }: { problem: ProblemPublic }) {
  return (
    <div>
      <h2 className="text-lg font-bold text-slate-900">{problem.title}</h2>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-600">
        {problem.spec}
      </p>
    </div>
  );
}
