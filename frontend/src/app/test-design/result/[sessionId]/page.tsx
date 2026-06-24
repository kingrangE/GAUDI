"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ProblemResultCard } from "../../../../components/ProblemResultCard";
import { ResultSummary } from "../../../../components/ResultSummary";
import { getResult } from "../../../../lib/api";
import type { ResultResponse } from "../../../../lib/types";

export default function ResultPage({ params }: { params: { sessionId: string } }) {
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getResult(params.sessionId)
      .then((r) => {
        if (active) setResult(r);
      })
      .catch(() => {
        if (active) setError("결과를 불러오지 못했습니다.");
      });
    return () => {
      active = false;
    };
  }, [params.sessionId]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl space-y-3">
        <p className="text-bad-600">{error}</p>
        <Link href="/test-design" className="text-sm font-medium text-brand-600 hover:text-brand-700">
          다시 시도 →
        </Link>
      </div>
    );
  }

  if (!result) {
    return <p className="text-slate-500">결과를 불러오는 중…</p>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <h1 className="text-2xl font-bold text-slate-900">평가 결과</h1>
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
