import { percent } from "./view";
import type { OverEngineeringItem } from "./types";
import styles from "./spec_design.module.css";

export function OverEngineeringList({ items }: { items: OverEngineeringItem[] }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <section className={styles.card} aria-label="요구사항 밖 과설계">
      <div className={styles.kicker}>요구사항 밖 과설계 ({items.length})</div>
      <p className={styles.muted}>요구사항에 없는데 일관되게 만들어진 기능 — 범위를 좁히세요.</p>
      <ul className={styles.reqList}>
        {items.map((item) => (
          <li key={item.label} className={styles.reqRow} data-tone="warn">
            <span className={styles.reqMark}>⚠</span>
            <span className={styles.reqText}>{item.label}</span>
            <span className={styles.reqRate}>{percent(item.prevalence)} 등장</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
