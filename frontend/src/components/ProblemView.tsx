import { Badge } from "@/components/ui/Badge";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { difficultyLabel, difficultyTone } from "@/lib/difficulty";
import type { ProblemPublic } from "../lib/types";

/** Problem brief: difficulty + title + the prose scenario, plus the basic tests
 *  already implemented (the candidate designs verification beyond these). */
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

      {problem.provided_tests.length > 0 ? (
        <div className="mt-4 rounded-lg border border-line bg-paper p-3">
          <SectionLabel>이미 구현된 기본 테스트</SectionLabel>
          <ul className="mt-2 space-y-1.5">
            {problem.provided_tests.map((test) => (
              <li key={test} className="flex items-start gap-2 text-sm text-ink-soft">
                <span className="text-good-600">✓</span>
                <span>{test}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
