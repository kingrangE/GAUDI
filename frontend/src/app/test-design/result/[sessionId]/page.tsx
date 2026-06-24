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
      <main>
        <p className="missed">{error}</p>
        <Link href="/test-design">다시 시도</Link>
      </main>
    );
  }

  if (!result) {
    return (
      <main>
        <p className="muted">결과를 불러오는 중…</p>
      </main>
    );
  }

  return (
    <main>
      <h1>평가 결과</h1>
      <ResultSummary result={result} />
      {result.problems.map((problem) => (
        <ProblemResultCard key={problem.problem_index} problem={problem} />
      ))}
      <Link href="/test-design">새 평가 시작</Link>
    </main>
  );
}
