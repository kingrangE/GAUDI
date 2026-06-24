import { Activity, CheckCircle2, Gauge } from "lucide-react";
import Link from "next/link";

import { AdminShell } from "@/components/admin/AdminShell";
import { USER_CODES } from "@/lib/accessCodes";
import {
  adminActivities,
  adminMetrics,
  candidateResults,
  trackDashboards,
  type AdminTone,
} from "@/lib/adminData";

import styles from "./page.module.css";

export const dynamic = "force-dynamic";

const toneClass: Record<AdminTone, string> = {
  teal: styles.teal,
  blue: styles.blue,
  amber: styles.amber,
  red: styles.red,
  green: styles.green,
};

export default function AdminPage() {
  const weaknessCount = candidateResults.reduce(
    (total, result) => total + result.weaknesses.length,
    0,
  );

  return (
    <AdminShell active="dashboard" eyebrow="해커톤 데모 운영" title="평가 현황 대시보드">
      <section className={styles.codePanel} aria-labelledby="entry-codes-title">
        <div className={styles.panelHeaderCompact}>
          <div>
            <p className={styles.eyebrow}>응시자 배포용</p>
            <h2 id="entry-codes-title">유저 입장 코드</h2>
          </div>
        </div>
        <p className={styles.codeHint}>
          아래 코드 중 하나를 응시자에게 전달하세요. 입장 화면에서 이 코드를 입력하면 응시자 페이지로
          진입합니다.
        </p>
        <ul className={styles.codeList}>
          {USER_CODES.map((code) => (
            <li className={styles.codeChip} key={code}>
              {code}
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.metricGrid} aria-label="관리 지표">
        {adminMetrics.map((metric) => (
          <article className={styles.metric} key={metric.id}>
            <div className={`${styles.metricIcon} ${toneClass[metric.tone]}`}>
              <Gauge aria-hidden="true" size={18} />
            </div>
            <p>{metric.label}</p>
            <strong>{metric.value}</strong>
            <span>{metric.detail}</span>
          </article>
        ))}
      </section>

      <div className={styles.contentGrid}>
        <section className={styles.panel} aria-labelledby="tracks-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>평가 축</p>
              <h2 id="tracks-title">항목별 대시보드</h2>
            </div>
          </div>

          <div className={styles.trackGrid}>
            {trackDashboards.map((track) => (
              <article className={styles.trackCard} key={track.id}>
                <div>
                  <p className={styles.eyebrow}>{track.shortName}</p>
                  <h3>{track.name}</h3>
                  <p>{track.description}</p>
                </div>
                <div className={styles.trackStats}>
                  <div>
                    <span>검토</span>
                    <strong>{track.pendingReviews}</strong>
                  </div>
                  <div>
                    <span>평균</span>
                    <strong>{track.averageScore}</strong>
                  </div>
                  <div>
                    <span>주의</span>
                    <strong>{track.flaggedCount}</strong>
                  </div>
                </div>
                <Link className={styles.linkButton} href={track.resultRoute}>
                  대시보드 보기
                </Link>
              </article>
            ))}
          </div>
        </section>

        <aside className={styles.sideStack}>
          <section className={styles.panel} aria-labelledby="decision-title">
            <div className={styles.panelHeaderCompact}>
              <h2 id="decision-title">리포트 요약</h2>
              <Activity aria-hidden="true" size={18} />
            </div>
            <div className={styles.decisionGrid}>
              <div>
                <span>응시자</span>
                <strong>{candidateResults.length}</strong>
              </div>
              <div>
                <span>보완 키워드</span>
                <strong>{weaknessCount}</strong>
              </div>
              <div>
                <span>평가 축</span>
                <strong>{trackDashboards.length}</strong>
              </div>
            </div>
          </section>

          <section className={styles.panel} aria-labelledby="result-location-title">
            <div className={styles.panelHeaderCompact}>
              <h2 id="result-location-title">결과 위치</h2>
              <span className={styles.badge}>2</span>
            </div>
            <div className={styles.resultLocation}>
              <strong>응시자 상세</strong>
              <span>개별 테스트 결과와 면접 질문 포인트</span>
            </div>
            <div className={styles.resultLocation}>
              <strong>축별 대시보드</strong>
              <span>평가 유형별 집계와 검토 우선순위</span>
            </div>
          </section>

          <section className={styles.panel} aria-labelledby="activity-title">
            <div className={styles.panelHeaderCompact}>
              <h2 id="activity-title">최근 활동</h2>
              <CheckCircle2 aria-hidden="true" size={18} />
            </div>
            <ol className={styles.activityList}>
              {adminActivities.map((activity) => (
                <li key={activity.id}>
                  <CheckCircle2 aria-hidden="true" size={16} />
                  <div>
                    <strong>{activity.actor}</strong>
                    <span>
                      {activity.action} · {activity.target}
                    </span>
                    <time>{activity.happenedAt}</time>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </aside>
      </div>
    </AdminShell>
  );
}
