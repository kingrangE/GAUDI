"use client";

import { useEffect, useState } from "react";

import { createRun, fetchProblem, fetchProblems, runTurn } from "./api";
import { CodePane } from "./CodePane";
import { ProblemPane } from "./ProblemPane";
import { PromptPane } from "./PromptPane";
import type { EvaluationView, ProblemPublic } from "./types";
import styles from "./workspace.module.css";

interface WorkspaceProps {
  problemId: string;
  // Provided by the server on assembly; otherwise the client fetches it.
  initialProblem?: ProblemPublic;
  /** When true: locks to problemId, hides picker, hides score/verdict, submits via onExamSubmit. */
  examMode?: boolean;
  examExpired?: boolean;
  /** Confirms the server-saved exam run using its prompt history. */
  onExamSubmit?: (prompts: string[]) => Promise<void>;
  onExamRun?: (prompt: string, turn: number) => Promise<EvaluationView>;
  loadExamRun?: () => Promise<EvaluationView>;
}

export function Workspace({ problemId, initialProblem, examMode, examExpired, onExamSubmit, onExamRun, loadExamRun }: WorkspaceProps) {
  const [currentId, setCurrentId] = useState(problemId);
  const [problem, setProblem] = useState<ProblemPublic | null>(initialProblem ?? null);
  const [problems, setProblems] = useState<ProblemPublic[]>([]);
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [result, setResult] = useState<EvaluationView | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Exam-only: whether the public test ledger is revealed, and whether a final
  // 제출 (hidden-case scoring) is in flight.
  const [showTests, setShowTests] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Load the problem list for the picker (best effort). Skipped in exam mode.
  useEffect(() => {
    if (examMode) return;
    let active = true;
    fetchProblems()
      .then((list) => {
        if (active && Array.isArray(list)) {
          setProblems(list);
        }
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [examMode]);

  useEffect(() => {
    if (!examMode || !loadExamRun) return;
    let active = true;
    loadExamRun().then((saved) => {
      if (!active) return;
      setResult(saved);
      setPrompts(saved.turns.map((t) => t.prompt));
      setPendingPrompt(saved.pending_prompt ?? null);
    }).catch(() => setError("저장된 실행을 불러오지 못했습니다."));
    return () => { active = false; };
  }, [examMode, loadExamRun]);

  // Load the selected problem (skip if the initial one was supplied).
  useEffect(() => {
    if (currentId === problemId && initialProblem) {
      setProblem(initialProblem);
      return;
    }
    let active = true;
    setProblem(null);
    fetchProblem(currentId)
      .then((p) => {
        if (active) {
          setProblem(p);
        }
      })
      .catch(() => {
        if (active) {
          setError("문제를 불러오지 못했습니다.");
        }
      });
    return () => {
      active = false;
    };
  }, [currentId, problemId, initialProblem]);

  function selectProblem(id: string) {
    if (id === currentId) {
      return;
    }
    setCurrentId(id);
    setPrompts([]);
    setPendingPrompt(null);
    setResult(null);
    setError(null);
    setShowTests(false);
  }

  // Each run adds one persisted turn; final submission confirms that same code.
  async function handleRun(prompt: string) {
    setRunning(true);
    setShowTests(false);
    setError(null);
    setPendingPrompt(prompt);
    try {
      let saved: EvaluationView;
      if (examMode) {
        if (!onExamRun) throw new Error("exam run callback is required");
        saved = await onExamRun(prompt, prompts.length + 1);
      } else {
        const run = result?.run_id ? result : await createRun(currentId);
        setResult(run);
        saved = await runTurn(run.run_id!, prompt, prompts.length + 1);
      }
      setResult(saved);
      setPrompts(saved.turns.map((t) => t.prompt));
      setPendingPrompt(null);
    } catch {
      setError("실행하지 못했습니다. 저장된 지시를 다시 실행해 주세요.");
    } finally {
      setRunning(false);
    }
  }

  // 테스트 채점: reveal the public (visible) test-case results for the latest run.
  function handleGradeTests() {
    if (!result) return;
    setShowTests(true);
  }

  // 제출: hand the accumulated prompts to the parent for the hidden-case (final)
  // scoring. On success the exam controller advances and unmounts us.
  async function handleFinalSubmit() {
    if (!onExamSubmit || prompts.length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await onExamSubmit(prompts);
    } catch {
      setError("제출에 실패했습니다. 다시 시도해주세요.");
      setSubmitting(false);
    }
  }

  const latestTurn =
    result && result.turns.length > 0 ? result.turns[result.turns.length - 1] : null;

  if (!problem) {
    return <div className={styles.loading}>{error ?? "문제를 불러오는 중…"}</div>;
  }

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <span className={styles.brand}>GAUDI</span>
        <span className={styles.feature}>PROMPT JUDGE</span>
        {!examMode && problems.length > 1 ? (
          <select
            className={styles.picker}
            aria-label="문제 선택"
            value={currentId}
            onChange={(e) => selectProblem(e.target.value)}
          >
            {problems.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
        ) : null}
        <span className={styles.spacer} />
        <span className={styles.attempts}>시도 {result?.turns.length ?? 0}</span>
      </header>
      <main className={styles.grid}>
        <ProblemPane problem={problem} />
        <CodePane code={latestTurn?.code ?? problem.starter_code} turn={latestTurn?.turn ?? null} />
        {pendingPrompt && !running && (
          <button onClick={() => void handleRun(pendingPrompt)} disabled={submitting}>
            저장된 지시 재실행
          </button>
        )}
        <PromptPane
          onSubmit={handleRun}
          running={running}
          blocked={Boolean(pendingPrompt) || examExpired}
          latestTurn={latestTurn}
          result={result}
          error={error}
          examMode={examMode}
          onGradeTests={handleGradeTests}
          onFinalSubmit={handleFinalSubmit}
          showTests={showTests}
          submitting={submitting}
          hasRun={Boolean(result?.turns.length) && !pendingPrompt}
        />
      </main>
    </div>
  );
}
