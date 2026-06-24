"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { getUserCode } from "@/lib/accessCodes";
import { DIFFICULTY_ORDER, difficultyLabel } from "@/lib/difficulty";
import { FlawListInput } from "../../components/FlawListInput";
import { ProblemView } from "../../components/ProblemView";
import { Timer } from "../../components/Timer";
import { createSession, submitProblem } from "../../lib/api";
import type { ProblemPublic } from "../../lib/types";

export default function TestDesignPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [problems, setProblems] = useState<ProblemPublic[]>([]);
  const [selected, setSelected] = useState(0);
  // Answers and submitted-state are kept per problem index so switching
  // problems via the dropdown never loses what the candidate typed.
  const [answers, setAnswers] = useState<Record<number, string[]>>({});
  const [submitted, setSubmitted] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // The candidate is already identified by the entry code, so start the
  // session automatically on entry — no name prompt.
  useEffect(() => {
    let active = true;
    createSession(getUserCode() ?? "anonymous")
      .then((session) => {
        if (!active) return;
        setSessionId(session.session_id);
        setProblems(session.problems);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError("세션을 시작하지 못했습니다. 백엔드가 실행 중인지 확인하세요.");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  // Group problems into difficulty tiers for the <optgroup> picker.
  const groups = useMemo(
    () =>
      DIFFICULTY_ORDER.map((d) => ({
        difficulty: d as string,
        items: problems.filter((p) => p.difficulty === d),
      })).filter((g) => g.items.length > 0),
    [problems],
  );

  const flaws = answers[selected] ?? [""];
  const setFlaws = (next: string[]) => setAnswers((prev) => ({ ...prev, [selected]: next }));

  async function submitCurrent() {
    if (!sessionId) return;
    const cleaned = flaws.map((f) => f.trim()).filter(Boolean);
    if (cleaned.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      await submitProblem(sessionId, selected, cleaned);
      setSubmitted((prev) => ({ ...prev, [selected]: true }));
    } catch {
      setError("채점 제출에 실패했습니다. 잠시 후 다시 시도하세요.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <p className="py-8 text-ink-soft">평가를 준비하는 중…</p>;
  }
  if (problems.length === 0) {
    return <p className="py-8 text-bad-600">{error ?? "문제를 불러오지 못했습니다."}</p>;
  }

  const problem = problems[selected];
  const submittedCount = Object.values(submitted).filter(Boolean).length;
  const cleanedCount = flaws.map((f) => f.trim()).filter(Boolean).length;
  const isSubmitted = Boolean(submitted[selected]);

  return (
    <div className="space-y-4 py-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-brand-600">테스트 설계</p>
          <h1 className="text-xl font-bold text-ink-900">테스트 설계 평가</h1>
        </div>
        <Timer />
      </div>

      <Panel className="flex flex-wrap items-center justify-between gap-3">
        <label htmlFor="problem-picker" className="flex items-center gap-2 text-sm">
          <span className="font-medium text-ink-900">문제 선택</span>
          <select
            id="problem-picker"
            aria-label="문제 선택"
            value={selected}
            onChange={(e) => setSelected(Number(e.target.value))}
            className="rounded-md border border-line bg-paper px-3 py-1.5 font-mono text-sm text-ink-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
          >
            {groups.map((g) => (
              <optgroup key={g.difficulty} label={difficultyLabel(g.difficulty)}>
                {g.items.map((p) => (
                  <option key={p.id} value={p.index}>
                    {submitted[p.index] ? "✓ " : ""}
                    {p.title}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>
        <div className="flex items-center gap-3 text-sm text-ink-soft">
          <span>
            제출 {submittedCount}/{problems.length}
          </span>
          <Button
            variant="secondary"
            disabled={submittedCount === 0}
            onClick={() => router.push(`/test-design/result/${sessionId}`)}
          >
            결과 보기
          </Button>
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        {/* Left — the prose scenario to verify */}
        <Panel className="min-h-0 overflow-y-auto">
          <ProblemView problem={problem} />
        </Panel>

        {/* Right — verification items */}
        <Panel className="flex min-h-0 flex-col">
          <SectionLabel>검증 항목</SectionLabel>
          <p className="mt-2 text-xs leading-relaxed text-ink-soft">
            이 기능 구현에서 반드시 확인·검증해야 할 항목을 한 줄에 하나씩 적으세요.
          </p>
          <div className="mt-3 min-h-0 flex-1 overflow-y-auto">
            <FlawListInput flaws={flaws} onChange={setFlaws} />
          </div>
          <div className="mt-4 flex items-center justify-between gap-2">
            {error ? (
              <span className="text-sm text-bad-600">{error}</span>
            ) : isSubmitted ? (
              <span className="text-sm text-good-600">제출됨 — 다시 제출하면 갱신됩니다.</span>
            ) : (
              <span />
            )}
            <Button disabled={busy || cleanedCount === 0} onClick={submitCurrent}>
              {busy ? "제출 중…" : isSubmitted ? "다시 제출" : "제출"}
            </Button>
          </div>
        </Panel>
      </div>
    </div>
  );
}
