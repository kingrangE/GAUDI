"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { createSession } from "@/features/rejection-eval/api";

export default function StartPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setLoading(true);
    setError(null);
    try {
      const session = await createSession();
      sessionStorage.setItem(
        `reval:topics:${session.session_id}`,
        JSON.stringify(session.topics),
      );
      router.push(`/rejection-eval/${session.session_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "세션 생성 실패");
      setLoading(false);
    }
  }

  return (
    <div className="py-8">
      <p className="text-sm font-semibold text-brand-600">거부 능력</p>
      <h1 className="mt-1 text-2xl font-bold text-ink-900">거부 능력 평가</h1>
      <p className="mt-2 text-ink-soft">
        고정 주제 3개에 대해, 제시된 기능 요구사항을 만족하도록 AI에게 설계를 지시하고,
        AI가 만든 설계 항목 중 잘못된 것·요구사항에 없는 것을 찾아내세요. 정밀도·재현율로 채점됩니다.
      </p>

      <Panel className="mt-6">
        <p className="text-sm text-ink-soft">
          준비가 되면 평가를 시작하세요. 세 개의 주제를 차례로 진행합니다.
        </p>
        <div className="mt-4">
          <Button onClick={start} disabled={loading}>
            {loading ? "시작 중…" : "평가 시작"}
          </Button>
        </div>
        {error ? <p className="mt-3 text-sm text-bad-600">{error}</p> : null}
      </Panel>
    </div>
  );
}
