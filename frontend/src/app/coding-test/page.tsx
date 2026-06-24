import { ProblemList } from "@/features/coding_test/components/ProblemList";

export default function CodingTestPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold text-slate-900">코딩 테스트</h1>
      <p className="mt-1 text-sm text-slate-500">
        문제를 골라 직접 풀고, 히든 케이스 채점과 코드 품질 분석을 받아보세요.
      </p>
      <div className="mt-6">
        <ProblemList />
      </div>
    </div>
  );
}
