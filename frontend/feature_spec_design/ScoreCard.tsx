import { gradeMeta, headline } from "./view";
import type { EvaluationResult } from "./types";
import styles from "./spec_design.module.css";

export function ScoreCard({ result }: { result: EvaluationResult }) {
  const { score } = result;
  const meta = gradeMeta(score.grade);

  return (
    <section className={styles.card} aria-label="명세 설계 점수">
      <div className={styles.kicker}>명세 설계 점수</div>
      <div className={styles.scoreHead}>
        <div className={styles.scoreNumber} data-tone={meta.tone}>
          {Math.round(score.total)}
        </div>
        <span className={styles.scoreOut}>/ 100</span>
        <span className={styles.badge} data-tone={meta.tone}>
          {meta.label}
        </span>
      </div>
      <p className={styles.headline}>{headline(result)}</p>
      <div className={styles.axes}>
        <span>
          요구사항 충족 <b>{Math.round(score.requirement_score)}</b>
        </span>
        <span>
          결정 품질 <b>{Math.round(score.decision_score)}</b>
        </span>
        <span>
          일관성 <b>{Math.round(score.consistency)}</b>
        </span>
        {score.overengineering_penalty > 0 ? (
          <span className={styles.penalty}>
            과설계 <b>−{Math.round(score.overengineering_penalty)}</b>
          </span>
        ) : null}
      </div>
      <p className={styles.feedbackText}>{score.feedback}</p>
    </section>
  );
}
