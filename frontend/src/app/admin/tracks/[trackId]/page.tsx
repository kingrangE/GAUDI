import Link from "next/link";
import { notFound } from "next/navigation";

import { AdminShell } from "@/components/admin/AdminShell";
import {
  candidateResults,
  getTrackDashboard,
  type EvaluationStatus,
  type TrackId,
} from "@/lib/adminData";

import styles from "../../sections.module.css";

export const dynamic = "force-dynamic";

type TrackPageProps = {
  params: Promise<{
    trackId: string;
  }>;
};

const routeToTrack: Record<string, TrackId> = {
  agent: "agent",
  office: "office",
  "coding-cs": "codingCs",
};

const statusLabels: Record<EvaluationStatus, string> = {
  pending: "대기",
  reviewing: "검토중",
  flagged: "확인 필요",
  done: "완료",
};

export default async function TrackDashboardPage({ params }: TrackPageProps) {
  const { trackId: trackParam } = await params;
  const trackId = routeToTrack[trackParam];

  if (!trackId) {
    notFound();
  }

  const track = getTrackDashboard(trackId);

  if (!track) {
    notFound();
  }

  return (
    <AdminShell active="dashboard" eyebrow={track.shortName} title={track.name}>
      <div className={styles.twoColumn}>
        <section className={styles.panel} aria-labelledby="track-tests-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>테스트 항목</p>
              <h2 id="track-tests-title">평가 구성</h2>
            </div>
            <span className={`${styles.status} ${styles.running}`}>집계</span>
          </div>

          <div className={styles.metaGrid}>
            <div>
              <span>검토 대기</span>
              <strong>{track.pendingReviews}</strong>
            </div>
            <div>
              <span>평균 점수</span>
              <strong>{track.averageScore}</strong>
            </div>
            <div>
              <span>확인 필요</span>
              <strong>{track.flaggedCount}</strong>
            </div>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>테스트 ID</th>
                  <th>항목</th>
                  <th>평가 지표</th>
                  <th>상태</th>
                </tr>
              </thead>
              <tbody>
                {track.tests.map((test) => (
                  <tr key={test.id}>
                    <td>{test.id}</td>
                    <td>{test.name}</td>
                    <td>{test.metric}</td>
                    <td>
                      <span className={`${styles.status} ${styles[test.status]}`}>
                        {statusLabels[test.status]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className={styles.grid}>
          <section className={styles.card}>
            <div>
              <p className={styles.eyebrow}>결과 확인</p>
              <h3>응시자별 리포트</h3>
            </div>
            <p className={styles.muted}>
              개별 테스트 결과는 응시자 상세 리포트에서 축별 점수와 근거로 확인한다.
            </p>
            <ul className={styles.tagList}>
              {candidateResults.map((candidate) => (
                <li key={candidate.id}>
                  <Link href={`/admin/results/${candidate.id}`}>{candidate.name}</Link>
                </li>
              ))}
            </ul>
          </section>

          <section className={styles.card}>
            <div>
              <p className={styles.eyebrow}>집계 관점</p>
              <h3>축별 대시보드</h3>
            </div>
            <p className={styles.muted}>{track.description}</p>
            <Link className={styles.link} href="/admin/results">
              전체 결과 보기
            </Link>
          </section>
        </aside>
      </div>
    </AdminShell>
  );
}
