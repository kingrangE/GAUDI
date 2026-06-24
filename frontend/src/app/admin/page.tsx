import { CheckCircle2, Clock, Gauge } from "lucide-react";
import Link from "next/link";

import { AdminShell } from "@/components/admin/AdminShell";
import { USER_CODES } from "@/lib/accessCodes";
import { fetchCandidates, formatScore, formatTime, statusLabel } from "@/lib/adminApi";

import styles from "./page.module.css";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const candidates = await fetchCandidates();

  const completed = candidates.filter(
    (c) => c.latest_attempt?.status === "completed",
  );
  const scores = completed
    .map((c) => c.latest_attempt?.overall_normalized)
    .filter((s): s is number => typeof s === "number");
  const averageScore = scores.length
    ? Math.round(scores.reduce((sum, s) => sum + s, 0) / scores.length)
    : null;

  const metrics = [
    {
      id: "completed",
      label: "모의고사 완료",
      value: `${completed.length}/${candidates.length || USER_CODES.length}`,
      detail: "응시자 기준",
      tone: styles.green,
      Icon: CheckCircle2,
    },
    {
      id: "average",
      label: "평균 점수",
      value: averageScore === null ? "—" : String(averageScore),
      detail: "완료 응시자 평균",
      tone: styles.teal,
      Icon: Gauge,
    },
    {
      id: "pending",
      label: "미완료",
      value: String((candidates.length || USER_CODES.length) - completed.length),
      detail: "미응시 또는 진행 중",
      tone: styles.amber,
      Icon: Clock,
    },
  ];

  return (
    <AdminShell active="dashboard" eyebrow="모의고사 운영" title="모의고사 결과 대시보드">
      <section className={styles.codePanel} aria-labelledby="entry-codes-title">
        <div className={styles.panelHeaderCompact}>
          <div>
            <p className={styles.eyebrow}>응시자 배포용</p>
            <h2 id="entry-codes-title">유저 입장 코드</h2>
          </div>
        </div>
        <p className={styles.codeHint}>
          아래 코드 중 하나를 응시자에게 전달하세요. 입장 화면에서 이 코드를 입력하면 응시자 페이지로
          진입합니다. (연습 결과는 기록·집계되지 않으며, 모의고사 결과만 아래에 표시됩니다.)
        </p>
        <ul className={styles.codeList}>
          {USER_CODES.map((code) => (
            <li className={styles.codeChip} key={code}>
              {code}
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.metricGrid} aria-label="모의고사 지표">
        {metrics.map((metric) => (
          <article className={styles.metric} key={metric.id}>
            <div className={`${styles.metricIcon} ${metric.tone}`}>
              <metric.Icon aria-hidden="true" size={18} />
            </div>
            <p>{metric.label}</p>
            <strong>{metric.value}</strong>
            <span>{metric.detail}</span>
          </article>
        ))}
      </section>

      <section className={styles.panel} aria-labelledby="candidates-title">
        <div className={styles.panelHeader}>
          <div>
            <p className={styles.eyebrow}>응시자</p>
            <h2 id="candidates-title">응시자별 모의고사 현황</h2>
          </div>
        </div>

        <div className={styles.trackGrid}>
          {candidates.map((candidate) => {
            const attempt = candidate.latest_attempt;
            const statusTone =
              attempt?.status === "completed" ? styles.done : styles.pending;
            return (
              <article className={styles.trackCard} key={candidate.code}>
                <div>
                  <p className={styles.eyebrow}>{candidate.code}</p>
                  <h3>{candidate.label}</h3>
                  <span className={`${styles.status} ${statusTone}`}>
                    {attempt ? statusLabel(attempt.status) : "미응시"}
                  </span>
                </div>
                <div className={styles.trackStats}>
                  <div>
                    <span>종합</span>
                    <strong>{formatScore(attempt?.overall_normalized ?? null)}</strong>
                  </div>
                  <div>
                    <span>완료</span>
                    <strong>{formatTime(attempt?.completed_at ?? null)}</strong>
                  </div>
                  <div>
                    <span>기능</span>
                    <strong>{attempt?.feature_count ?? 0}</strong>
                  </div>
                </div>
                {attempt ? (
                  <Link className={styles.linkButton} href={`/admin/results/${attempt.id}`}>
                    리포트 보기
                  </Link>
                ) : (
                  <span className={styles.codeHint}>아직 응시 기록이 없습니다.</span>
                )}
              </article>
            );
          })}
          {candidates.length === 0 ? (
            <p className={styles.codeHint}>
              백엔드에 연결할 수 없거나 아직 모의고사 응시 기록이 없습니다.
            </p>
          ) : null}
        </div>
      </section>
    </AdminShell>
  );
}
