"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getResult, scoreSession } from "@/features/rejection-eval/api";
import { ItemVerdictTable } from "@/features/rejection-eval/components/ItemVerdictTable";
import { ScorePanel } from "@/features/rejection-eval/components/ScorePanel";
import type { ResultResponse } from "@/features/rejection-eval/types";

export default function RejectionResultPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    // On first visit the session isn't scored yet — getResult returns 409, so we
    // run scoring here (the slow LLM judge). Re-visits hit the already-scored
    // result and skip re-scoring.
    getResult(sessionId)
      .then((r) => {
        if (active) setResult(r);
      })
      .catch(() =>
        scoreSession(sessionId)
          .then((r) => {
            if (active) setResult(r);
          })
          .catch(() => {
            if (active) setError("채점에 실패했습니다.");
          }),
      );
    return () => {
      active = false;
    };
  }, [sessionId]);

  if (error) {
    return (
      <div className="space-y-3 py-2">
        <p className="text-bad-600">{error}</p>
        <Link
          href="/rejection-eval"
          className="text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          다시 시도 →
        </Link>
      </div>
    );
  }
  if (!result) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex items-center gap-3 py-16 text-ink-soft"
      >
        <Loader2 className="h-6 w-6 animate-spin text-brand-600" aria-hidden />
        <span>채점 중…</span>
      </div>
    );
  }

  const topic = result.topics[0];

  return (
    <div className="space-y-5 py-2">
      <h1 className="text-2xl font-bold text-ink-900">거부 능력 평가 결과</h1>
      {topic ? (
        <>
          <p className="text-sm text-ink-soft">
            주제: <strong className="text-ink-900">{topic.topic_title}</strong>
          </p>
          <ScorePanel topic={topic} />
          <ItemVerdictTable items={topic.items} />
        </>
      ) : (
        <p className="text-ink-soft">표시할 결과가 없습니다.</p>
      )}
      <Link
        href="/rejection-eval"
        className="inline-block text-sm font-medium text-brand-600 hover:text-brand-700"
      >
        새 평가 시작 →
      </Link>
    </div>
  );
}
