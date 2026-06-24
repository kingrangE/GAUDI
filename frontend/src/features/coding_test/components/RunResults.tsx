import { Badge } from "@/components/ui/Badge";
import { SectionLabel } from "@/components/ui/SectionLabel";
import type { RunResponse } from "../types";

export function RunResults({
  data,
  isPending,
}: {
  data?: RunResponse;
  isPending: boolean;
}) {
  if (isPending) return <p className="text-sm text-ink-soft">샘플 테스트 실행 중…</p>;
  if (!data) return null;

  const passed = data.results.filter((r) => r.passed).length;
  return (
    <div>
      <div className="flex items-center justify-between">
        <SectionLabel>샘플 실행</SectionLabel>
        <Badge tone={passed === data.results.length ? "good" : "warn"}>
          샘플 결과: {passed}/{data.results.length} 통과
        </Badge>
      </div>
      <ul className="mt-2 space-y-1 text-sm">
        {data.results.map((r) => (
          <li key={r.index} className="flex items-center gap-2">
            <span className={r.passed ? "text-good-600" : "text-bad-600"}>
              {r.passed ? "●" : "○"}
            </span>
            <span className={r.passed ? "text-ink-soft" : "text-bad-700"}>
              케이스 {r.index + 1}: {r.passed ? "통과" : `실패${r.error ? ` (${r.error})` : ""}`}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
