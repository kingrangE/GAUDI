"use client";

import { useEffect, useState } from "react";

import { fetchTasks, runEvaluation } from "./api";
import { DimensionTable } from "./DimensionTable";
import { InstructionForm } from "./InstructionForm";
import { OverEngineeringList } from "./OverEngineeringList";
import { RequirementsList } from "./RequirementsList";
import { SampleList } from "./SampleList";
import { ScoreCard } from "./ScoreCard";
import { TaskPicker } from "./TaskPicker";
import type { EvaluationResult, TaskPublic } from "./types";
import styles from "./spec_design.module.css";

interface WorkbenchProps {
  /** When true, locks to examTaskId, hides picker and result pane, and routes submit to onExamSubmit. */
  examMode?: boolean;
  /** Task ID to lock to in exam mode (e.g. "cx-churn-radar-topn"). */
  examTaskId?: string;
  /** Called with the typed instruction when the user submits in exam mode. */
  onExamSubmit?: (instruction: string) => Promise<void>;
}

export function Workbench({ examMode, examTaskId, onExamSubmit }: WorkbenchProps = {}) {
  const [tasks, setTasks] = useState<TaskPublic[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(examMode ? (examTaskId ?? null) : null);
  const [instruction, setInstruction] = useState("");
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchTasks()
      .then((list) => {
        if (active && Array.isArray(list)) {
          setTasks(list);
          // In exam mode pin selection to the supplied task id.
          if (examMode && examTaskId) setSelectedId(examTaskId);
        }
      })
      .catch(() => {
        if (active) setError("과제를 불러오지 못했습니다. 백엔드 연결을 확인하세요.");
      });
    return () => {
      active = false;
    };
  }, [examMode, examTaskId]);

  const selectedTask = tasks.find((t) => t.id === selectedId) ?? null;

  function selectTask(id: string) {
    setSelectedId(id);
    setResult(null);
    setError(null);
  }

  async function submit() {
    if (!selectedTask) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      if (examMode && onExamSubmit) {
        await onExamSubmit(instruction);
      } else {
        setResult(await runEvaluation(selectedTask.id, instruction));
      }
    } catch {
      setError("평가에 실패했습니다. 백엔드 연결을 확인하세요.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <span className={styles.brand}>GAUDI</span>
        <span className={styles.feature}>SPEC DESIGN</span>
        <span className={styles.spacer} />
        <span className={styles.topbarNote}>명세 설계 · 답변 일관성</span>
      </header>
      <div className={examMode ? styles.splitExam : styles.split}>
        <section className={`${styles.pane} ${styles.paneLeft}`} aria-label="과제와 지시">
          {!examMode && (
            <>
              <div className={styles.kicker}>과제 선택</div>
              <TaskPicker tasks={tasks} selectedId={selectedId} onSelect={selectTask} />
            </>
          )}
          {examMode && error ? (
            <div className={styles.error} role="alert">
              {error}
            </div>
          ) : null}
          {selectedTask ? (
            <div className={examMode ? undefined : styles.paneSection}>
              <InstructionForm
                brief={selectedTask.brief}
                value={instruction}
                onChange={setInstruction}
                onSubmit={submit}
                loading={running}
              />
            </div>
          ) : null}
        </section>
        {!examMode && (
          <section className={`${styles.pane} ${styles.paneRight}`} aria-label="평가 결과">
            <div className={styles.kicker}>평가 결과</div>
            {error ? (
              <div className={styles.error} role="alert">
                {error}
              </div>
            ) : null}
            {running ? <p className={styles.paneHintRunning}>지시를 평가하는 중…</p> : null}
            {!running && !error && !result ? (
              <p className={styles.paneHint}>왼쪽에서 과제를 고르고 지시를 작성해 평가하세요.</p>
            ) : null}
            {result ? (
              <>
                <ScoreCard result={result} />
                <RequirementsList requirements={result.requirements} />
                <OverEngineeringList items={result.overengineering} />
                <DimensionTable dimensions={result.dimensions} />
                <SampleList samples={result.samples} />
              </>
            ) : null}
          </section>
        )}
      </div>
    </div>
  );
}
