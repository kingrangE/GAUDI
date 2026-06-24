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
  }

  async function handleSubmit(prompt: string) {
    const next = [...prompts, prompt];
    setPrompts(next);
    setRunning(true);
    setError(null);
    try {
      if (examMode) {
        if (onExamSubmit) await onExamSubmit(next);
      } else {
        setResult(await runEvaluation(currentId, next));
      }
    } catch {
      setError("채점에 실패했습니다. 백엔드 연결을 확인하세요.");
    } finally {
      setRunning(false);
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
        <span className={styles.brand}>and·you</span>
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
          onSubmit={handleSubmit}
          running={running}
          latestTurn={latestTurn}
          result={result}
          error={error}
          examMode={examMode}
        />
      </main>
    </div>
  );
}
