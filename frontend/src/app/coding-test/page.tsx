import { ProblemList } from "@/features/coding_test/components/ProblemList";

export default function CodingTestPage() {
  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-2xl font-bold">코딩 테스트</h1>
      <ProblemList />
    </main>
  );
}
