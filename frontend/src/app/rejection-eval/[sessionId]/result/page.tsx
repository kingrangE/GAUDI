"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getResult } from "@/features/rejection-eval/api";
import { OutcomeBadge } from "@/features/rejection-eval/components/OutcomeBadge";
import type { ResultResponse } from "@/features/rejection-eval/types";

function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

function Metrics({ precision, recall, f1 }: { precision: number; recall: number; f1: number }) {
  return (
    <p style={{ fontWeight: 600 }}>
      Precision {pct(precision)} · Recall {pct(recall)} · F1 {pct(f1)}
    </p>
  );
}

export default function ResultPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getResult(sessionId)
      .then(setResult)
      .catch((e) => setError(e instanceof Error ? e.message : "결과 조회 실패"));
  }, [sessionId]);

  if (error) return <main><p style={{ color: "#c5221f" }}>{error}</p></main>;
  if (!result) return <main><p>결과를 불러오는 중…</p></main>;

  return (
    <main>
      <h1>거부 능력 평가 결과</h1>
      <p>
        응시자: <strong>{result.candidate_name}</strong>
      </p>
      <h2>전체</h2>
      <Metrics precision={result.precision} recall={result.recall} f1={result.f1} />

      {result.topics.map((topic) => (
        <section key={topic.topic_index} style={{ marginTop: 24 }}>
          <h3>
            주제 {topic.topic_index + 1}. {topic.topic_title}
          </h3>
          <Metrics precision={topic.precision} recall={topic.recall} f1={topic.f1} />
          {topic.report && <p style={{ fontStyle: "italic" }}>📝 {topic.report}</p>}
          <ul style={{ listStyle: "none", padding: 0 }}>
            {topic.items.map((item) => (
              <li key={item.id} style={{ marginBottom: 10 }}>
                <OutcomeBadge outcome={item.outcome} />{" "}
                <span>{item.text}</span>
                <div style={{ color: "#5f6368", fontSize: 14 }}>{item.explanation}</div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </main>
  );
}
