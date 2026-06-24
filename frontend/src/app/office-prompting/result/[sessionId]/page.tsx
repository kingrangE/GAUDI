"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { scoreSession } from "@/features/office-prompting/api";
import { ResultSummary } from "@/features/office-prompting/components/ResultSummary";
import type { ResultResponse } from "@/features/office-prompting/types";

export default function OfficePromptingResultPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    scoreSession(sessionId)
      .then((r) => active && setResult(r))
      .catch(() => active && setError("채점에 실패했습니다. 모든 문제를 실행했는지 확인하세요."));
    return () => {
      active = false;
    };
  }, [sessionId]);

  if (error) {
    return <p className="py-8 text-bad-600">{error}</p>;
  }
  if (!result) {
    return (
      <div className="flex items-center gap-3 py-8 text-ink-soft">
        <Spinner />
        채점하는 중…
      </div>
    );
  }
  return <ResultSummary result={result} />;
}
