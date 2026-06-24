import { notFound } from "next/navigation";

import { AdminShell } from "@/components/admin/AdminShell";
import { getCandidateResult } from "@/lib/adminData";

import styles from "../../sections.module.css";

export const dynamic = "force-dynamic";

type CandidateResultPageProps = {
  params: {
    candidateId: string;
  };
};

const trackLabels = {
  agentRejection: "AI 거부 능력",
  specDesign: "명세 설계",
  contextEngineering: "Context Engineering",
  codingCs: "코테/CS",
  officePrompting: "사무직 Prompting",
};

export default function CandidateResultPage({ params }: CandidateResultPageProps) {
  const result = getCandidateResult(params.candidateId);

  if (!result) {
    notFound();
  }

  const trackEntries = Object.entries(result.tracks) as Array<
    [keyof typeof trackLabels, number]
  >;

  return (
    <AdminShell active="results" eyebrow="개인 진단" title={`${result.name} 평가 리포트`}>
      <div className={styles.twoColumn}>
        <section className={styles.panel} aria-labelledby="score-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>{result.role}</p>
              <h2 id="score-title">역량별 점수</h2>
            </div>
            <span className={styles.badge}>종합 {result.totalScore}</span>
          </div>

          <div className={styles.metaGrid}>
            <div>
              <span>종합 점수</span>
              <strong>{result.totalScore}</strong>
            </div>
            <div>
              <span>강점</span>
              <strong>{result.strengths.length}</strong>
            </div>
            <div>
              <span>보완 필요</span>
              <strong>{result.weaknesses.length}</strong>
            </div>
          </div>

          <ul className={styles.scoreList}>
            {trackEntries.map(([track, score]) => (
              <li key={track}>
                <span>{trackLabels[track]}</span>
                <div className={styles.progressTrack}>
                  <div className={styles.progressFill} style={{ width: `${score}%` }} />
                </div>
                <strong>{score}</strong>
              </li>
            ))}
          </ul>
        </section>

        <aside className={styles.grid}>
          <section className={styles.card}>
            <div>
              <p className={styles.eyebrow}>요약 리포트</p>
              <h3>강점 키워드</h3>
            </div>
            <ul className={styles.tagList}>
              {result.strengths.map((strength) => (
                <li key={strength}>{strength}</li>
              ))}
            </ul>
          </section>

          <section className={styles.card}>
            <div>
              <p className={styles.eyebrow}>분석 리포트</p>
              <h3>보완 필요 키워드</h3>
            </div>
            <ul className={styles.tagList}>
              {result.weaknesses.map((weakness) => (
                <li key={weakness}>{weakness}</li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </AdminShell>
  );
}
