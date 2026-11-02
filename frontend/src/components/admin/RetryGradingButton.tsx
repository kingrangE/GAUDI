"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui";
import { mockExamApi } from "@/features/mock_exam/api";

export function RetryGradingButton({ attemptId, featureKey }: {
  attemptId: string; featureKey: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return <>
    <Button disabled={busy} onClick={async () => {
      setBusy(true);
      setError("");
      try {
        await mockExamApi.retryStep(attemptId, featureKey);
        router.refresh();
      } catch {
        setError("재채점하지 못했습니다. 진행 중인 작업은 잠시 후 다시 확인하세요.");
      } finally {
        setBusy(false);
      }
    }}>{busy ? "채점 중…" : "저장된 답안 재채점"}</Button>
    {error && <p role="alert">{error}</p>}
  </>;
}
