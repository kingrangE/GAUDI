import { SolvePanel } from "@/features/coding_test/components/SolvePanel";

export default async function SolvePage({ params }: { params: Promise<{ problemId: string }> }) {
  const { problemId } = await params;
  return <SolvePanel problemId={problemId} />;
}
