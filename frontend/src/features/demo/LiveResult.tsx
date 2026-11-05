"use client";

import { useQuery } from "@tanstack/react-query";
import { Badge, Button, CodePanel, Metric } from "@/components/ui";
import { ResultSummary } from "@/components/ResultSummary";
import { ProblemResultCard } from "@/components/ProblemResultCard";
import type { ResultResponse as TestReport } from "@/lib/types";
import { ResultView } from "@/features/cs_eval/components/ResultView";
import type { SessionResult } from "@/features/cs_eval/types";
import { ResultCards } from "@/features/coding_test/components/ResultCards";
import { RunResults as CodeRuns } from "@/features/coding_test/components/RunResults";
import type { SubmissionResult, RunResponse as CodeRun } from "@/features/coding_test/types";
import { RunResults as OfficeRuns } from "@/features/office-prompting/components/RunResults";
import type { ResultResponse as OfficeReport, RunResponse as OfficeRun } from "@/features/office-prompting/types";
import { ScorePanel } from "@/features/rejection-eval/components/ScorePanel";
import type { ResultResponse as RejectionReport, GenerateResponse } from "@/features/rejection-eval/types";
import { ScoreCard } from "../../../feature_spec_design/ScoreCard";
import { RequirementsList } from "../../../feature_spec_design/RequirementsList";
import { DimensionTable } from "../../../feature_spec_design/DimensionTable";
import { OverEngineeringList } from "../../../feature_spec_design/OverEngineeringList";
import type { EvaluationResult as SpecReport } from "../../../feature_spec_design/types";
import type { EvaluationReport } from "../../../feature_context_engineering/types";
import type { EvaluationView } from "../../../feature_dev_prompting/types";
import type { Activity } from "./tracking";

function object(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? value as Record<string, unknown> : {};
}
function id(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9_-]{1,128}$/.test(value);
}

function savedReport(activity: Activity): string | undefined {
  const data = object(activity.result?.body);
  const feature = activity.state?.feature;
  if (feature === "cs_eval" && id(data.session_id)) return `/api/cs-eval/sessions/${data.session_id}`;
  if (feature === "coding_test" && id(data.submission_id)) return `/api/coding-test/submissions/${data.submission_id}`;
  if (feature === "test_design" && activity.state?.action === "submit") {
    const session = activity.path?.match(/^\/test-design\/sessions\/([A-Za-z0-9_-]+)\/problems\/\d+\/submit$/)?.[1];
    if (id(session)) return `/test-design/sessions/${session}/result`;
  }
}

export function LiveResult({ activity }: { activity: Activity }) {
  const endpoint = savedReport(activity);
  const remote = useQuery({
    queryKey: ["demo-saved-report", activity.owner, activity.id, endpoint],
    enabled: Boolean(endpoint), retry: false,
    queryFn: async () => {
      const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
      const response = await fetch(`${base}${endpoint}`, { credentials: "include", cache: "no-store" });
      if (!response.ok) throw new Error("saved report unavailable");
      return response.json() as Promise<unknown>;
    },
  });
  if (endpoint && remote.isPending) return <p role="status">저장된 리포트를 불러오는 중입니다.</p>;
  if (endpoint && remote.isError) return (
    <div className="space-y-2"><p role="alert">저장된 리포트에 연결하지 못했습니다.</p>
      <Button variant="secondary" onClick={() => void remote.refetch()}>리포트 다시 조회</Button></div>
  );
  const body = object(endpoint ? remote.data : activity.result?.body);
  const { feature, action } = activity.state ?? {};
  // Exam status/recording acknowledgements never become a score report, even after finish.
  if (feature === "mock_exam") return (
    <p className="text-sm text-ink-soft">
      {body.completed === true ? "모의고사 제출이 완료되었습니다." : "시험 작업이 저장되었습니다. 시험 화면에서 이어서 진행하세요."}
      {" "}점수와 정답은 이 화면에 표시하지 않습니다.
    </p>
  );
  if (feature === "context_engineering" && Array.isArray(body.dimensions)) {
    const report = body as unknown as EvaluationReport;
    return <div className="space-y-3"><Metric label="종합 점수" value={report.total} hint="/ 100" />
      {report.dimensions.map((axis) => <div key={axis.key} className="text-sm">
        <Badge tone="neutral">{axis.label}: {axis.available ? axis.score : "미채점"}</Badge>
        <p className="mt-1 text-ink-soft">{axis.detail}</p></div>)}
      <ul className="space-y-1 text-sm">{report.results.map((row) => <li key={row.id}>
        {row.covered ? "충족" : "누락"}: {row.text}{row.evidence ? ` — ${row.evidence}` : ""}</li>)}</ul>
    </div>;
  }
  if (feature === "spec_design" && body.score) {
    const report = body as unknown as SpecReport;
    return <div className="space-y-3"><ScoreCard result={report} />
      <RequirementsList requirements={report.requirements} /><DimensionTable dimensions={report.dimensions} />
      <OverEngineeringList items={report.overengineering} /></div>;
  }
  if (feature === "cs_eval" && Array.isArray(body.per_question)) return <ResultView result={body as unknown as SessionResult} />;
  if (feature === "coding_test") {
    if (Array.isArray(body.results)) return <CodeRuns data={body as unknown as CodeRun} isPending={false} />;
    if (body.status) return <ResultCards result={body as unknown as SubmissionResult} isPending={false} />;
  }
  if (feature === "dev_prompting" && Array.isArray(body.turns)) {
    const report = body as unknown as EvaluationView;
    const latest = report.turns.at(-1);
    return <div className="space-y-3">
      {report.score && <Metric label="평가 점수" value={report.score.total} hint="/ 100" />}
      {latest ? <><p className="text-sm">{latest.turn}번째 실행 결과 · {latest.feedback}</p>
        <CodePanel label="이번 실행에서 생성한 코드" code={latest.code} /></> : <p>개발 체험이 준비되었습니다.</p>}
    </div>;
  }
  if (feature === "office_prompting" && Array.isArray(body.predicted_rows)) {
    const run = body as unknown as OfficeRun;
    return <OfficeRuns rows={run.predicted_rows} columns={Object.keys(run.predicted_rows[0] ?? {})} hasRun />;
  }
  if (feature === "office_prompting" && action === "score") {
    const report = body as unknown as OfficeReport;
    return <div className="space-y-2"><Metric label="F1" value={Math.round(report.f1 * 100)} hint="/ 100" />
      {report.problems.map((problem) => <p key={problem.problem_index} className="text-sm">
        {problem.title}: 정밀도 {Math.round(problem.precision * 100)}%, 재현율 {Math.round(problem.recall * 100)}%</p>)}</div>;
  }
  if (feature === "rejection_eval" && Array.isArray(body.items)) {
    return <ul className="space-y-2 text-sm">{(body as unknown as GenerateResponse).items.map((item) => <li key={item.id}>{item.text}</li>)}</ul>;
  }
  if (feature === "rejection_eval" && Array.isArray(body.topics)) {
    return <div className="space-y-3">{(body as unknown as RejectionReport).topics.map((topic) => <ScorePanel key={topic.topic_index} topic={topic} />)}</div>;
  }
  if (feature === "test_design" && Array.isArray(body.problems) && "weighted_score" in body) {
    const report = body as unknown as TestReport;
    return <div className="space-y-3"><ResultSummary result={report} />
      {report.problems.map((problem) => <ProblemResultCard key={problem.problem_index} problem={problem} />)}</div>;
  }
  return <p className="text-sm text-ink-soft">작업이 저장되었습니다. 원래 화면에서 체험을 이어서 진행할 수 있습니다.</p>;
}
