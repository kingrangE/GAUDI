"use client";

import { useEffect, useState } from "react";

import { fetchProblem, fetchProblems, runEvaluation } from "./api";
import { CodePane } from "./CodePane";
import { ProblemPane } from "./ProblemPane";
import { PromptPane } from "./PromptPane";
import type { EvaluationResult, ProblemPublic } from "./types";
import styles from "./workspace.module.css";

interface WorkspaceProps {
  problemId: string;
  // Provided by the server on assembly; otherwise the client fetches it.
  initialProblem?: ProblemPublic;
  /** When true: locks to problemId, hides picker, hides score/verdict, submits via onExamSubmit. */
  examMode?: boolean;
  /** Called instead of runEvaluation when examMode is true. Receives all accumulated prompts. */
  onExamSubmit?: (prompts: string[]) => Promise<void>;
}

export function Workspace({ problemId, initialProblem, examMode, onExamSubmit }: WorkspaceProps) {
  const [currentId, setCurrentId] = useState(problemId);
  const [problem, setProblem] = useState<ProblemPublic | null>(initialProblem ?? null);
  const [problems, setProblems] = useState<ProblemPublic[]>([]);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [result, setResult] = useState<EvaluationResult | null>(null);
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
    setResult(null);
    setError(null);
    setShowTests(false);
  }

  // 실행: add the prompt as a new turn and run it through the judge so the
  // candidate sees the agent's code. In exam mode this is *not* the submission —
  // the final score comes from 제출 below. (Practice mode also routes here.)
  async function handleRun(prompt: string) {
    const next = [...prompts, prompt];
    setPrompts(next);
    setRunning(true);
    setShowTests(false); // a fresh run invalidates the previously revealed ledger
    setError(null);
    try {
      setResult(await runEvaluation(currentId, next));
    } catch {
      setError(
        examMode
          ? "실행에 실패했습니다. 백엔드 연결을 확인하세요."
          : "채점에 실패했습니다. 백엔드 연결을 확인하세요.",
      );
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
        <PromptPane
          onSubmit={handleRun}
          running={running}
          latestTurn={latestTurn}
          result={result}
          error={error}
          examMode={examMode}
          onGradeTests={handleGradeTests}
          onFinalSubmit={handleFinalSubmit}
          showTests={showTests}
          submitting={submitting}
          hasRun={result !== null}
        />
      </main>
    </div>
  );
}
