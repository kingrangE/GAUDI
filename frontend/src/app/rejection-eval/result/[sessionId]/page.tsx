"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getResult } from "@/features/rejection-eval/api";
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
    getResult(sessionId)
      .then((r) => {
        if (active) setResult(r);
      })
      .catch(() => {
        if (active) setError("결과를 불러오지 못했습니다.");
      });
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
    return <p className="py-8 text-ink-soft">결과를 불러오는 중…</p>;
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
