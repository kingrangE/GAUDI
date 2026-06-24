import { CsEvalResult } from "@/features/cs_eval/components/CsEvalResult";

export default async function CsEvalResultPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;
  return <CsEvalResult sessionId={sessionId} />;
}
