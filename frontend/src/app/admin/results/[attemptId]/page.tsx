import { notFound } from "next/navigation";

import { AdminShell } from "@/components/admin/AdminShell";
import { FeaturePanel } from "@/components/admin/FeaturePanel";
import { Badge, Metric } from "@/components/ui";
import {
  EXAM_FLOW,
  STEP_LABELS,
  fetchExamResult,
  formatElapsed,
  formatScore,
  statusLabel,
  type AttemptStatus,
} from "@/lib/adminApi";

import styles from "../../sections.module.css";

export const dynamic = "force-dynamic";

type AttemptResultPageProps = {
  params: Promise<{ attemptId: string }>;
};

function statusBadgeTone(status: AttemptStatus): "good" | "warn" | "bad" {
  switch (status) {
    case "completed":
      return "good";
    case "in_progress":
      return "warn";
    case "failed":
      return "bad";
  }
}

export default async function AttemptResultPage({ params }: AttemptResultPageProps) {
  const { attemptId } = await params;
  const detail = await fetchExamResult(attemptId);

  if (!detail) {
    notFound();
  }

  // Sort features in exam-flow order; unknown keys go to the end.
  const flowIndex = (key: string) => {
    const idx = (EXAM_FLOW as readonly string[]).indexOf(key);
    return idx === -1 ? 99 : idx;
  };
  const orderedFeatures = [...detail.features].sort(
    (a, b) => flowIndex(a.feature_key) - flowIndex(b.feature_key),
  );

  return (
    <AdminShell
      active="results"
      eyebrow="모의고사 리포트"
      title={`${detail.candidate_label} 모의고사 리포트`}
    >
      {/* Summary header */}
      <section className={styles.panel} aria-labelledby="summary-title">
        <div className={styles.panelHeader}>
          <div>
            <p className={styles.eyebrow}>{detail.candidate_code}</p>
            <h2 id="summary-title" style={{ margin: 0 }}>
              시험 요약
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone={statusBadgeTone(detail.status)}>{statusLabel(detail.status)}</Badge>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Metric
            label="종합 점수"
            value={formatScore(detail.overall_normalized)}
            hint="0–100 정규화"
          />
          <Metric
            label="완료 시간"
            value={
              detail.completed_at
                ? new Date(detail.completed_at).toLocaleTimeString("ko-KR", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "—"
            }
          />
          <Metric
            label="소요 시간"
            value={formatElapsed(detail.started_at, detail.completed_at)}
          />
          <Metric label="평가 기능" value={`${detail.features.length}개`} />
        </div>
      </section>

      {/* Per-step overview bar */}
      {orderedFeatures.length > 0 ? (
        <section className={styles.panel} aria-labelledby="steps-overview-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>5단계 점수</p>
              <h2 id="steps-overview-title" style={{ margin: 0 }}>
                단계별 정규화 점수
              </h2>
            </div>
          </div>
          <div className="grid gap-3">
            {EXAM_FLOW.map((key) => {
              const feature = orderedFeatures.find((f) => f.feature_key === key);
              const score = feature?.normalized_score ?? null;
              const label = STEP_LABELS[key];
              return (
                <div key={key} className="grid grid-cols-[180px_minmax(0,1fr)_52px] items-center gap-3">
                  <span className="text-sm font-medium text-ink-soft">{label}</span>
                  <div className="h-2 overflow-hidden rounded-full bg-paper">
                    <div
                      className={
                        score === null
                          ? "h-full rounded-full bg-line"
                          : score >= 70
                            ? "h-full rounded-full bg-good-600"
                            : score >= 40
                              ? "h-full rounded-full bg-brand-600"
                              : "h-full rounded-full bg-bad-600"
                      }
                      style={{ width: score !== null ? `${score}%` : "0%" }}
                      role="presentation"
                    />
                  </div>
                  <span className="text-right font-mono text-sm tabular-nums text-ink-soft">
                    {score !== null ? `${Math.round(score)}` : "—"}
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      {/* Rich per-feature panels */}
      <div className="grid gap-5" aria-label="단계별 상세 결과">
        {orderedFeatures.map((feature) => (
          <FeaturePanel key={feature.feature_key} feature={feature} />
        ))}
        {orderedFeatures.length === 0 ? (
          <p className={styles.muted}>기록된 기능 결과가 없습니다.</p>
        ) : null}
      </div>
    </AdminShell>
  );
}
