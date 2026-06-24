import type { TurnResult } from "./types";
import { verdictFor } from "./verdict";
import styles from "./workspace.module.css";

interface VerdictLedgerProps {
  turn: TurnResult | null;
  running: boolean;
}

export function VerdictLedger({ turn, running }: VerdictLedgerProps) {
  if (running) {
    return <div className={styles.ledgerRunning}>채점 중…</div>;
  }
  if (!turn) {
    return <div className={styles.ledgerEmpty}>채점 결과가 여기에 표시됩니다.</div>;
  }
  return (
    <div className={styles.ledger} aria-label="채점 결과">
      <div className={styles.ledgerSummary}>
        통과 {turn.passed_count}/{turn.total}
      </div>
      <ul className={styles.caseList}>
        {turn.case_results.map((c) => {
          const v = verdictFor(c.status);
          return (
            <li key={c.index} className={styles.caseRow} data-tone={v.tone}>
              <span className={styles.caseName}>
                {c.hidden ? "숨김" : "예제"} #{c.index}
              </span>
              <span className={styles.caseVerdict}>{v.short}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
