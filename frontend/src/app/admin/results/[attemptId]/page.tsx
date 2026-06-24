import { notFound } from "next/navigation";

import { AdminShell } from "@/components/admin/AdminShell";
import {
  fetchExamResult,
  formatScore,
  formatTime,
  statusLabel,
} from "@/lib/adminApi";

import styles from "../../sections.module.css";

export const dynamic = "force-dynamic";

type AttemptResultPageProps = {
  params: Promise<{ attemptId: string }>;
};

export default async function AttemptResultPage({ params }: AttemptResultPageProps) {
  const { attemptId } = await params;
  const detail = await fetchExamResult(attemptId);

  if (!detail) {
    notFound();
  }

  return (
    <AdminShell
      active="results"
      eyebrow="모의고사 리포트"
      title={`${detail.candidate_label} 모의고사 리포트`}
    >
      <div className={styles.twoColumn}>
        <section className={styles.panel} aria-labelledby="score-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>{detail.candidate_code}</p>
              <h2 id="score-title">기능별 점수</h2>
            </div>
            <span className={styles.badge}>
              종합 {formatScore(detail.overall_normalized)}
            </span>
          </div>

          <div className={styles.metaGrid}>
            <div>
              <span>상태</span>
              <strong>{statusLabel(detail.status)}</strong>
            </div>
            <div>
              <span>완료 시간</span>
              <strong>{formatTime(detail.completed_at)}</strong>
            </div>
            <div>
              <span>평가 기능</span>
              <strong>{detail.features.length}</strong>
            </div>
          </div>

          <ul className={styles.scoreList}>
            {detail.features.map((feature) => (
              <li key={feature.feature_key}>
                <span>{feature.label}</span>
                <div className={styles.progressTrack}>
                  <div
                    className={styles.progressFill}
                    style={{ width: `${Math.round(feature.normalized_score)}%` }}
                  />
                </div>
                <strong>{Math.round(feature.normalized_score)}</strong>
              </li>
            ))}
            {detail.features.length === 0 ? (
              <li>
                <span className={styles.muted}>기록된 기능 결과가 없습니다.</span>
              </li>
            ) : null}
          </ul>
        </section>

        <aside className={styles.grid}>
          {detail.features.map((feature) => (
            <section className={styles.card} key={feature.feature_key}>
              <div>
                <p className={styles.eyebrow}>
                  {feature.label} · {Math.round(feature.normalized_score)}점
                </p>
                <h3>{feature.summary ? "요약" : "결과"}</h3>
              </div>
              <p className={styles.muted}>
                {feature.summary ?? "세부 요약이 제공되지 않았습니다."}
              </p>
            </section>
          ))}
        </aside>
      </div>
    </AdminShell>
  );
}
