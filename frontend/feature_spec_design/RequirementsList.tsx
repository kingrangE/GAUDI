import { requirementsBySatisfaction } from "./view";
import type { RequirementResult } from "./types";
import styles from "./spec_design.module.css";

export function RequirementsList({ requirements }: { requirements: RequirementResult[] }) {
  if (requirements.length === 0) {
    return null;
  }
  const rows = requirementsBySatisfaction(requirements);
  const met = requirements.filter((r) => r.satisfied).length;

  return (
    <section className={styles.card} aria-label="요구사항 충족">
      <div className={styles.kicker}>
        요구사항 충족 ({met}/{requirements.length})
      </div>
      <ul className={styles.reqList}>
        {rows.map((req) => (
          <li key={req.id} className={styles.reqRow} data-tone={req.satisfied ? "great" : "bad"}>
            <span className={styles.reqMark}>{req.satisfied ? "✓" : "✗"}</span>
            <span className={styles.reqText}>{req.text}</span>
            <span className={styles.reqRate}>
              {req.met_count}/{req.total}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
