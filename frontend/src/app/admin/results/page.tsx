import { AdminShell } from "@/components/admin/AdminShell";
import { ResultsTable } from "@/components/admin/ResultsTable";
import { fetchExamResults } from "@/lib/adminApi";

import styles from "../sections.module.css";

export const dynamic = "force-dynamic";

export default async function ResultsPage() {
  const attempts = await fetchExamResults();

  const completed = attempts.filter((a) => a.status === "completed");
  const scores = completed
    .map((a) => a.overall_normalized)
    .filter((s): s is number => typeof s === "number");
  const averageScore = scores.length
    ? Math.round(scores.reduce((sum, s) => sum + s, 0) / scores.length)
    : "—";

  return (
    <AdminShell active="results" eyebrow="모의고사 진단" title="응시자별 모의고사 결과">
      <div className={styles.grid}>
        <section className={styles.panel} aria-label="리포트 요약">
          <div className={styles.metaGrid}>
            <div>
              <span>응시 건수</span>
              <strong>{attempts.length}</strong>
            </div>
            <div>
              <span>완료</span>
              <strong>{completed.length}</strong>
            </div>
            <div>
              <span>평균 점수</span>
              <strong>{averageScore}</strong>
            </div>
          </div>
        </section>

        <section className={styles.panel} aria-labelledby="results-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>모의고사 진단</p>
              <h2 id="results-title">종합 리포트</h2>
            </div>
          </div>

          <ResultsTable attempts={attempts} />
        </section>
      </div>
    </AdminShell>
  );
}
