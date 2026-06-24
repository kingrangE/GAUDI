"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { CodeMeta, CodePanel } from "@/components/ui/CodePanel";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { FlawListInput } from "../../components/FlawListInput";
import { ProblemView } from "../../components/ProblemView";
import { ProgressBar } from "../../components/ProgressBar";
import { Timer } from "../../components/Timer";
import { createSession, submitProblem } from "../../lib/api";
import type { ProblemPublic } from "../../lib/types";

export default function TestDesignPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [problems, setProblems] = useState<ProblemPublic[]>([]);
  const [index, setIndex] = useState(0);
  const [flaws, setFlaws] = useState<string[]>([""]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const session = await createSession(name.trim());
      setSessionId(session.session_id);
      setProblems(session.problems);
      setIndex(0);
      setFlaws([""]);
    } catch {
      setError("세션을 시작하지 못했습니다. 백엔드가 실행 중인지 확인하세요.");
    } finally {
      setBusy(false);
    }
  }

  async function submitCurrent() {
    if (!sessionId) return;
    const cleaned = flaws.map((f) => f.trim()).filter(Boolean);
    if (cleaned.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      await submitProblem(sessionId, index, cleaned);
      if (index + 1 >= problems.length) {
        router.push(`/test-design/result/${sessionId}`);
      } else {
        setIndex(index + 1);
        setFlaws([""]);
      }
    } catch {
      setError("채점 제출에 실패했습니다. 잠시 후 다시 시도하세요.");
    } finally {
      setBusy(false);
    }
  }

  // -- Start screen ----------------------------------------------------------
  if (!sessionId) {
    return (
      <div className="py-8">
        <p className="text-sm font-semibold text-brand-600">테스트 설계</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">테스트 설계 평가</h1>
        <p className="mt-2 text-slate-600">
          주어진 코드의 숨은 결함을 찾아내는 검증 역량을 평가합니다. 총 5개의 코드 문제가
          출제됩니다.
        </p>
        <Panel className="mt-6">
          <label htmlFor="candidate" className="block text-sm font-medium text-slate-700">
            응시자 이름
          </label>
          <input
            id="candidate"
            type="text"
            value={name}
            placeholder="응시자 이름"
            aria-label="응시자 이름"
            onChange={(e) => setName(e.target.value)}
            className="mt-2 w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          />
          <div className="mt-4">
            <Button disabled={busy || name.trim().length === 0} onClick={start}>
              {busy ? "시작 중…" : "시작"}
            </Button>
          </div>
          {error ? <p className="mt-3 text-sm text-bad-600">{error}</p> : null}
        </Panel>
      </div>
    );
  }

  // -- Per-problem session ---------------------------------------------------
  const problem = problems[index];
  const cleanedCount = flaws.map((f) => f.trim()).filter(Boolean).length;
  const isLast = index + 1 >= problems.length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">테스트 설계 평가</h1>
        <Timer />
      </div>
      <ProgressBar current={index + 1} total={problems.length} />

      <div className="grid h-[calc(100vh-12rem)] grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)_minmax(0,1fr)] gap-4">
        {/* Left — problem brief */}
        <Panel className="min-h-0 overflow-y-auto">
          <ProblemView problem={problem} />
        </Panel>

        {/* Center — code under review (dark) */}
        <CodePanel label="CODE UNDER REVIEW" meta={<CodeMeta>python</CodeMeta>} code={problem.code} />

        {/* Right — flaw input */}
        <Panel className="flex min-h-0 flex-col">
          <SectionLabel>발견한 결함</SectionLabel>
          <p className="mt-2 text-xs leading-relaxed text-slate-500">
            코드가 명세를 어기는 지점·경계 상황을 한 항목씩 서술하세요.
          </p>
          <div className="mt-3 min-h-0 flex-1 overflow-y-auto">
            <FlawListInput flaws={flaws} onChange={setFlaws} />
          </div>
          <div className="mt-3 flex items-center justify-between">
            {error ? <span className="text-sm text-bad-600">{error}</span> : <span />}
            <Button disabled={busy || cleanedCount === 0} onClick={submitCurrent}>
              {busy ? "제출 중…" : isLast ? "제출하고 결과 보기" : "제출하고 다음 문제"}
            </Button>
          </div>
        </Panel>
      </div>
    </div>
  );
}
