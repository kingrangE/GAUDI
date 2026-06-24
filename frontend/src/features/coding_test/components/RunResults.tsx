import type { RunResponse } from "../types";

export function RunResults({
  data,
  isPending,
}: {
  data?: RunResponse;
  isPending: boolean;
}) {
  if (isPending) return <p className="text-sm text-slate-500">샘플 테스트 실행 중…</p>;
  if (!data) return null;

  const passed = data.results.filter((r) => r.passed).length;
  return (
    <div className="text-sm">
      <p className="mb-2 font-medium">
        샘플 결과: {passed}/{data.results.length} 통과
      </p>
      <ul className="space-y-1">
        {data.results.map((r) => (
          <li key={r.index} className={r.passed ? "text-green-700" : "text-red-700"}>
            케이스 {r.index + 1}: {r.passed ? "통과" : `실패${r.error ? ` (${r.error})` : ""}`}
          </li>
        ))}
      </ul>
    </div>
  );
}
