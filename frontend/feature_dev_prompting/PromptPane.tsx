import { useState } from "react";

import type { EvaluationResult, TurnResult } from "./types";
import { VerdictLedger } from "./VerdictLedger";
import styles from "./workspace.module.css";

interface PromptPaneProps {
  onSubmit: (prompt: string) => void;
  running: boolean;
  latestTurn: TurnResult | null;
  result: EvaluationResult | null;
  error: string | null;
  /** When true: hides score, verdict ledger, and feedback (scoring is server-side in exam). */
  examMode?: boolean;
}

export function PromptPane({ onSubmit, running, latestTurn, result, error, examMode }: PromptPaneProps) {
  const [draft, setDraft] = useState("");
  const canSubmit = draft.trim().length > 0 && !running;

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
        placeholder="에이전트에게 풀이 방법을 지시하세요. 코드는 직접 수정할 수 없습니다. (⌘/Ctrl+Enter로 채점)"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
            submit();
          }
        }}
        disabled={running}
        rows={5}
      />
      <button className={styles.runButton} onClick={submit} disabled={!canSubmit}>
        {running ? "채점 중…" : "채점 실행"}
      </button>
      {error ? <div className={styles.error}>{error}</div> : null}
      {!examMode && result?.solved ? (
        <div className={styles.solved}>맞았습니다 · {result.score.total}점</div>
      ) : null}
      {!examMode ? <VerdictLedger turn={latestTurn} running={running} /> : null}
      {!examMode && latestTurn && !latestTurn.solved && latestTurn.feedback ? (
        <pre className={styles.feedback}>{latestTurn.feedback}</pre>
      ) : null}
    </section>
  );
}
