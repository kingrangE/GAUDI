import { dimensionStatus, dimensionTone, dimensionsByScore, percent } from "./view";
import type { DimensionResult } from "./types";
import styles from "./spec_design.module.css";

export function DimensionTable({ dimensions }: { dimensions: DimensionResult[] }) {
  const rows = dimensionsByScore(dimensions);

  return (
    <section className={styles.card} aria-label="설계 결정 평가">
      <div className={styles.kicker}>설계 결정 평가</div>
      <table className={styles.dimTable}>
        <thead>
          <tr>
            <th>설계 결정</th>
            <th>선택</th>
            <th>일치도</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((dim) => (
            <tr key={dim.key} data-tone={dimensionTone(dim)}>
              <td>{dim.label}</td>
              <td>{dim.top_value}</td>
              <td>
                <div className={styles.barRow}>
                  <div className={styles.bar}>
                    <span className={styles.barFill} style={{ width: percent(dim.agreement) }} />
                  </div>
                  <span>{percent(dim.agreement)}</span>
                </div>
              </td>
              <td className={styles.verdict}>{dimensionStatus(dim)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
