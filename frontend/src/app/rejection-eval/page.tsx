"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { createSession } from "@/features/rejection-eval/api";

export default function StartPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const session = await createSession(name.trim());
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
    <div className="mx-auto max-w-xl py-8">
      <p className="text-sm font-semibold text-brand-600">거부 능력</p>
      <h1 className="mt-1 text-2xl font-bold text-slate-900">거부 능력 평가</h1>
      <p className="mt-2 text-slate-600">
        고정 주제 3개에 대해 AI에게 설계를 지시하고, AI가 만든 설계 항목 중 잘못된 것을
        찾아내세요. 정밀도·재현율로 채점됩니다.
      </p>

      <Panel className="mt-6">
        <label htmlFor="candidate" className="block text-sm font-medium text-slate-700">
          응시자 이름
        </label>
        <input
          id="candidate"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="이름을 입력하세요"
          className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
        />
        <div className="mt-4">
          <Button onClick={start} disabled={loading || !name.trim()}>
            {loading ? "시작 중…" : "평가 시작"}
          </Button>
        </div>
        {error ? <p className="mt-3 text-sm text-bad-600">{error}</p> : null}
      </Panel>
    </div>
  );
}
