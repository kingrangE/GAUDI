"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { Button, Panel, SectionLabel } from "@/components/ui";
import { ProgressBar } from "@/components/ProgressBar";
import { recoverPending } from "./jobs";
import { isDemoEnabled } from "./session";
import { dismiss, getOwner, getServerSnapshot, getSnapshot, observe, subscribe, type Activity } from "./tracking";
import { SampleReport } from "./SampleReport";
import { LiveResult } from "./LiveResult";

const LABELS: Record<string, string> = {
  context_engineering: "컨텍스트 엔지니어링", spec_design: "명세 설계", dev_prompting: "개발 프롬프팅",
  coding_test: "코딩 테스트", cs_eval: "CS 평가", office_prompting: "업무 프롬프팅",
  rejection_eval: "거부 능력", test_design: "테스트 설계", mock_exam: "모의고사",
};
const PHASES: Record<string, string> = {
  queued: "실행 순서를 기다리는 중", evaluating: "평가 준비 및 실행 중",
  static_checks: "문서 근거와 기본 규칙 확인", coverage: "요구사항 커버리지 확인",
  boundary: "경계 조건 확인", generating_samples: "여러 구현 생성 중",
  analyzing_samples: "생성된 구현 비교·채점 중", aggregating_score: "평가 점수 정리 중",
  running_tests: "코드 테스트 실행 중", code_analysis: "코드 품질 분석 중",
  grading_answers: "문항별 답변 채점 중", synthesizing_report: "종합 리포트 작성 중",
  generating_design: "검토할 설계안 생성 중", grading_topics: "제출한 판단 채점 중",
  extracting_data: "요청한 데이터 추출 중", matching_flaws: "검증 항목과 결함 대조 중",
  generating_code: "코드 생성 및 실행 중", testing_turn: "생성 코드 테스트 중", completed: "저장된 결과를 가져오는 중",
};
function report(activity: Activity) {
  const { feature, action } = activity.state ?? {};
  return feature !== "mock_exam" && ["evaluate", "post_submission", "score", "submit", "create_submission"].includes(action ?? "") ||
    feature === "cs_eval" && action === "create_session";
}

function JobCard({ activity }: { activity: Activity }) {
  const state = activity.state;
  const ready = Boolean(activity.result);
  const title = ready ? report(activity) ? "Live Report" : "이번 작업의 실제 결과" : "실제 결과를 기다리고 있습니다";
  const phase = activity.error ? "작업 상태 확인 필요" : state?.status === "queued" ? PHASES.queued
    : PHASES[state?.phase ?? ""] ?? "작업을 처리하고 있습니다";
  return (
    <Panel className="space-y-4" aria-label={`${LABELS[state?.feature ?? ""] ?? "체험"} 작업`}>
      <div className="flex items-start justify-between gap-2">
        <div><SectionLabel>{LABELS[state?.feature ?? ""] ?? "포트폴리오 체험"}</SectionLabel>
          <h2 className="mt-1 font-semibold">{title}</h2></div>
        {(ready || activity.error) && <Button variant="ghost" onClick={() => dismiss(activity.id)}>닫기</Button>}
      </div>
      <p role="status" className="text-sm text-ink-soft">{ready ? "이번 작업에서 서버에 저장한 실제 결과입니다." : phase}</p>
      {!activity.error && <ProgressBar current={ready ? 1 : state?.completed_units ?? 0} total={ready ? 1 : state?.total_units ?? 0}
        maxPercent={ready ? 100 : 99} label="작업 진행"
        indeterminate={!ready && (!state || state.status === "queued" || !state.completed_units)} />}
      {!ready && <p className="text-xs text-ink-soft">진행률은 완료된 처리 단위의 비율이며 남은 시간의 예측이 아닙니다. 한 단계가 오래 걸릴 수 있습니다.</p>}
      {activity.error && <div className="space-y-2">
        <p role="alert" className="text-sm text-bad-700">{activity.error}</p>
        {activity.lastPhase && PHASES[activity.lastPhase] && <p className="text-xs text-ink-soft">
          마지막 확인 단계: {PHASES[activity.lastPhase]}</p>}
        {state?.status !== "failed" && <Button variant="secondary"
          onClick={() => void observe(activity.id, activity.owner, activity.path).catch(() => {})}>조회 다시 연결</Button>}
      </div>}
      {ready ? <LiveResult activity={activity} /> : <SampleReport feature={state?.feature} />}
    </Panel>
  );
}

export function JobActivity() {
  const jobs = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const [collapsed, setCollapsed] = useState(false);
  const [restoreError, setRestoreError] = useState(false);
  const [restoreAttempt, setRestoreAttempt] = useState(0);
  useEffect(() => {
    if (!isDemoEnabled()) return;
    let active = true;
    const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
    const previousOwner = getOwner();
    // Reading the current cookie never issues a new visitor merely for opening a page.
    void fetch(`${base}/api/demo/session`, { credentials: "include", cache: "no-store" })
      .then(async (response) => {
        if (!active) return;
        if (response.status === 401) { setRestoreError(false); return; }
        if (!response.ok) throw new Error("session lookup failed");
        setRestoreError(false);
        const visitor = await response.json() as { session_id: string };
        const currentOwner = getOwner();
        if (currentOwner !== previousOwner && currentOwner !== visitor.session_id) return;
        if (active && /^[a-f0-9]{32}$/.test(visitor.session_id)) void recoverPending(visitor.session_id);
      }).catch(() => { if (active) setRestoreError(true); });
    return () => { active = false; };
  }, [restoreAttempt]);
  const visible = [...jobs].reverse().filter((job) => !job.result ||
    !(job.state?.action === "create_run" || job.state?.action === "create_session" && job.state?.feature !== "cs_eval"));
  if (!isDemoEnabled() || (!visible.length && !restoreError)) return null;
  return (
    <aside aria-label="체험 작업 현황" className="fixed inset-x-3 bottom-3 z-50 mx-auto max-h-[85vh] max-w-3xl overflow-y-auto rounded-lg border border-line bg-paper p-3 shadow-panel sm:left-auto sm:right-4 sm:w-[min(44rem,calc(100vw-2rem))]">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="text-sm font-medium">체험 작업 {visible.length}개</span>
        <Button variant="ghost" aria-expanded={!collapsed} onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? "작업 현황 펼치기" : "접어두고 둘러보기"}
        </Button>
      </div>
      {restoreError && <Panel className="mb-3 space-y-2">
        <p role="alert" className="text-sm text-ink-soft">이전 작업을 확인하지 못했습니다. 연결 후 다시 조회할 수 있습니다.</p>
        <Button variant="secondary" onClick={() => setRestoreAttempt((value) => value + 1)}>이전 작업 다시 확인</Button>
      </Panel>}
      {!collapsed && <div className="space-y-3">{visible.map((activity) => <JobCard key={activity.id} activity={activity} />)}</div>}
    </aside>
  );
}
