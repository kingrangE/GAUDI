import ReactMarkdown from "react-markdown";

import type { ProblemDetail } from "../types";
import { CountdownTimer } from "./CountdownTimer";

export function ProblemPane({
  problem,
  timerSeconds,
}: {
  problem: ProblemDetail;
  timerSeconds: number;
}) {
  return (
    <div className="flex h-full flex-col p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">{problem.title}</h1>
        <div className="flex items-center gap-3">
          <span className="rounded bg-slate-200 px-2 py-0.5 text-xs uppercase">
            {problem.difficulty}
          </span>
          <CountdownTimer seconds={timerSeconds} />
        </div>
      </div>
      <article className="space-y-2 text-sm leading-relaxed">
        <ReactMarkdown>{problem.description_md}</ReactMarkdown>
      </article>
    </div>
  );
}
