"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

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

  if (!sessionId) {
    return (
      <main>
        <h1>테스트 설계 평가</h1>
        <div className="panel">
          <p>이름을 입력하고 평가를 시작하세요. 총 5개의 코드 문제가 출제됩니다.</p>
          <div className="row">
            <input
              type="text"
              value={name}
              placeholder="응시자 이름"
              aria-label="응시자 이름"
              onChange={(e) => setName(e.target.value)}
            />
            <button className="primary" disabled={busy || name.trim().length === 0} onClick={start}>
              {busy ? "시작 중…" : "시작"}
            </button>
          </div>
          {error ? <p className="missed">{error}</p> : null}
        </div>
      </main>
    );
  }

  const problem = problems[index];
  const cleanedCount = flaws.map((f) => f.trim()).filter(Boolean).length;
  const isLast = index + 1 >= problems.length;

  return (
    <main>
      <div className="spread">
        <h1>테스트 설계 평가</h1>
        <Timer />
      </div>
      <ProgressBar current={index + 1} total={problems.length} />
      <ProblemView problem={problem} />
      <div className="panel">
        <h3>발견한 결함을 적어주세요</h3>
        <p className="muted">코드가 명세를 어기는 지점·경계 상황을 한 항목씩 서술하세요.</p>
        <FlawListInput flaws={flaws} onChange={setFlaws} />
        <div className="spread" style={{ marginTop: "1rem" }}>
          {error ? <span className="missed">{error}</span> : <span />}
          <button className="primary" disabled={busy || cleanedCount === 0} onClick={submitCurrent}>
            {busy ? "제출 중…" : isLast ? "제출하고 결과 보기" : "제출하고 다음 문제"}
          </button>
        </div>
      </div>
    </main>
  );
}
