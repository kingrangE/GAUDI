"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { ProblemResultCard } from "../../../../components/ProblemResultCard";
import { ResultSummary } from "../../../../components/ResultSummary";
import {
  getResult,
  pendingSubmissionKey,
  submitProblem,
  type PendingSubmission,
} from "../../../../lib/api";
import type { ResultResponse } from "../../../../lib/types";

export default function ResultPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [grading, setGrading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function run() {
      // A submission handed off from the solve page is graded here so the
      // candidate sees the grading spinner straight after pressing submit.
      const key = pendingSubmissionKey(sessionId);
      const raw = typeof window !== "undefined" ? sessionStorage.getItem(key) : null;
      if (raw) {
        sessionStorage.removeItem(key);
        if (active) setGrading(true);
        try {
          const pending = JSON.parse(raw) as PendingSubmission;
          await submitProblem(sessionId, pending.index, pending.flaws);
        } catch {
          if (active) {
            setError("채점에 실패했습니다. 잠시 후 다시 시도하세요.");
            setGrading(false);
          }
          return;
        }
        if (active) setGrading(false);
      }

      try {
        const r = await getResult(sessionId);
        if (active) setResult(r);
      } catch {
        if (active) setError("결과를 불러오지 못했습니다.");
      }
    }

    run();
    return () => {
      active = false;
    };
  }, [sessionId]);

  if (error) {
    return (
      <div className="space-y-3 py-8">
        <p className="text-bad-600">{error}</p>
        <Link href="/test-design" className="text-sm font-medium text-brand-600 hover:text-brand-700">
          다시 시도 →
        </Link>
      </div>
    );
  }

  // Grading in progress (or the result hasn't loaded yet) → circular indicator.
  if (grading || !result) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
        <Spinner className="h-10 w-10" label="채점 중" />
        <div>
          <p className="font-medium text-ink-900">{grading ? "채점 중입니다…" : "결과를 불러오는 중…"}</p>
          {grading ? (
            <p className="mt-1 text-sm text-ink-soft">
              AI가 작성하신 검증 항목을 채점하고 있습니다. 잠시만 기다려 주세요.
            </p>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-ink-900">평가 결과</h1>
      <ResultSummary result={result} />
      {result.problems.map((problem) => (
        <ProblemResultCard key={problem.problem_index} problem={problem} />
      ))}
      <Link href="/test-design" className="inline-block text-sm font-medium text-brand-600 hover:text-brand-700">
        새 평가 시작 →
      </Link>
    </div>
  );
}
