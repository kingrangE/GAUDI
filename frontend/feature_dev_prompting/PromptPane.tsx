import { useState } from "react";

import type { EvaluationResult, TurnResult } from "./types";
import { VerdictLedger } from "./VerdictLedger";
import styles from "./workspace.module.css";

interface PromptPaneProps {
  /** Runs the prompt: practice mode scores it; exam mode just implements the code. */
  onSubmit: (prompt: string) => void;
  running: boolean;
  latestTurn: TurnResult | null;
  result: EvaluationResult | null;
  error: string | null;
  /** When true: hides the overall score/feedback and swaps in the 실행·테스트 채점·제출 controls. */
  examMode?: boolean;
  /** Exam: reveal the public (visible) test-case results for the latest run. */
  onGradeTests?: () => void;
  /** Exam: submit the accumulated prompts for the hidden-case (final) scoring. */
  onFinalSubmit?: () => void;
  /** Exam: whether the public test ledger is currently revealed. */
  showTests?: boolean;
  /** Exam: a 제출 request is in flight. */
  submitting?: boolean;
  /** Exam: at least one 실행 has produced code (enables 테스트 채점 / 제출). */
  hasRun?: boolean;
}

export function PromptPane({
  onSubmit,
  running,
  latestTurn,
  result,
  error,
  examMode,
  onGradeTests,
  onFinalSubmit,
  showTests,
  submitting,
  hasRun,
}: PromptPaneProps) {
  const [draft, setDraft] = useState("");
  const busy = running || Boolean(submitting);
  const canSubmit = draft.trim().length > 0 && !busy;

  function submit() {
    if (!canSubmit) {
      return;
    }
    onSubmit(draft.trim());
    setDraft("");
  }

  return (
    <section className={styles.prompt} aria-label="지시">
      <div className={styles.kicker}>INSTRUCT THE AGENT</div>
      <textarea
        className={styles.promptInput}
        placeholder={
          examMode
            ? "에이전트에게 풀이 방법을 지시하세요. 코드는 직접 수정할 수 없습니다. (⌘/Ctrl+Enter로 실행)"
            : "에이전트에게 풀이 방법을 지시하세요. 코드는 직접 수정할 수 없습니다. (⌘/Ctrl+Enter로 채점)"
        }
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
            submit();
          }
        }}
        disabled={busy}
        rows={5}
      />
      {examMode ? (
        // 실행 → 코드 구현, 테스트 채점 → 공개 테스트 점수, 제출 → 히든 채점(최종).
        <div className={styles.buttonRow}>
          <button className={styles.runButton} onClick={submit} disabled={!canSubmit}>
            {running ? "실행 중…" : "실행"}
          </button>
          <button
            className={styles.secondaryButton}
            onClick={onGradeTests}
            disabled={!hasRun || busy}
          >
            테스트 채점
          </button>
          <button
            className={styles.submitButton}
            onClick={onFinalSubmit}
            disabled={!hasRun || busy}
          >
            {submitting ? "제출 중…" : "제출"}
          </button>
        </div>
      ) : (
        <button className={styles.runButton} onClick={submit} disabled={!canSubmit}>
          {running ? "채점 중…" : "채점 실행"}
        </button>
      )}
      {error ? <div className={styles.error}>{error}</div> : null}
      {/* Practice mode: full score + every-case verdict + feedback. */}
      {!examMode && result?.solved ? (
        <div className={styles.solved}>맞았습니다 · {result.score.total}점</div>
      ) : null}
      {!examMode ? <VerdictLedger turn={latestTurn} running={running} /> : null}
      {!examMode && latestTurn && !latestTurn.solved && latestTurn.feedback ? (
        <pre className={styles.feedback}>{latestTurn.feedback}</pre>
      ) : null}
      {/* Exam mode: public-only test results, revealed on 테스트 채점. */}
      {examMode && showTests ? (
        <VerdictLedger turn={latestTurn} running={running} publicOnly />
      ) : null}
    </section>
  );
}
