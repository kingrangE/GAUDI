import { AdminShell } from "@/components/admin/AdminShell";
import { ResultsTable } from "@/components/admin/ResultsTable";
import { candidateResults } from "@/lib/adminData";

import styles from "../sections.module.css";

export const dynamic = "force-dynamic";

const averageScore = Math.round(
  candidateResults.reduce((total, result) => total + result.totalScore, 0) /
    candidateResults.length,
);

const weaknessCount = candidateResults.reduce(
  (total, result) => total + result.weaknesses.length,
  0,
);

export default function ResultsPage() {
  return (
    <AdminShell active="results" eyebrow="진단 리포트" title="응시자별 평가 결과">
      <div className={styles.grid}>
        <section className={styles.panel} aria-label="리포트 요약">
          <div className={styles.metaGrid}>
            <div>
              <span>응시자</span>
              <strong>{candidateResults.length}</strong>
            </div>
            <div>
              <span>평균 점수</span>
              <strong>{averageScore}</strong>
            </div>
            <div>
              <span>보완 키워드</span>
              <strong>{weaknessCount}</strong>
            </div>
          </div>
        </section>

        <section className={styles.panel} aria-labelledby="results-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>개인별 진단</p>
              <h2 id="results-title">종합 리포트</h2>
            </div>
          </div>

          <ResultsTable />
        </section>

        <section className={styles.cardGrid} aria-label="추가 운영 기능">
          <article className={styles.card}>
            <div>
              <p className={styles.eyebrow}>다음 기능</p>
              <h3>필터</h3>
            </div>
            <p className={styles.muted}>
              평가 축, 보완 키워드, 점수 구간, 세션별로 결과를 좁혀야 한다.
            </p>
          </article>
          <article className={styles.card}>
            <div>
              <p className={styles.eyebrow}>다음 기능</p>
              <h3>리포트 내보내기</h3>
            </div>
            <p className={styles.muted}>
              심사위원 공유용 PDF와 내부 분석용 CSV 다운로드가 필요하다.
            </p>
          </article>
        </section>
      </div>
    </AdminShell>
  );
}
