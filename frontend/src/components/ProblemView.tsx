import { Badge } from "@/components/ui/Badge";
import { difficultyLabel, difficultyTone } from "@/lib/difficulty";
import type { ProblemPublic } from "../lib/types";

/** Problem brief: difficulty + title + the prose scenario to be verified. */
export function ProblemView({ problem }: { problem: ProblemPublic }) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <Badge tone={difficultyTone(problem.difficulty)}>{difficultyLabel(problem.difficulty)}</Badge>
        <h2 className="text-lg font-bold text-ink-900">{problem.title}</h2>
      </div>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink-soft">
        {problem.spec}
      </p>
    </div>
  );
}
