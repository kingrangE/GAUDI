import { SolvePanel } from "@/features/coding_test/components/SolvePanel";

export default function SolvePage({ params }: { params: { problemId: string } }) {
  return <SolvePanel problemId={params.problemId} />;
}
