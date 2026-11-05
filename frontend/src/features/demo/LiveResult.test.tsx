import { cleanup, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, expect, it, vi } from "vitest";
import { LiveResult } from "./LiveResult";
import type { Activity } from "./tracking";

const base = { id: "a".repeat(32), owner: "visitor" };
function show(feature: string, action: string, body: unknown, path?: string) {
  const activity: Activity = { ...base, path, state: { feature, action, status: "completed" }, result: { http_status: 200, body } };
  return render(<QueryClientProvider client={new QueryClient()}><LiveResult activity={activity} /></QueryClientProvider>);
}
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it.each(["start", "submit_step", "run_dev_turn", "generate_rejection_items", "finish"])(
  "never renders exam scores, ground truth or hidden-case output for %s", (action) => {
    show("mock_exam", action, { score: 99, total: 99, report: "secret judgement", correct: "secret answer",
      turns: [{ code: "private code", feedback: "secret feedback" }], completed: action === "finish" });
    expect(screen.getByText(/점수와 정답은 이 화면에 표시하지 않습니다/)).toBeTruthy();
    expect(screen.queryByText(/99|secret|private/)).toBeNull();
    expect(screen.queryByText("Live Report")).toBeNull();
  },
);

it("shows generated practice code rather than an invented final score", () => {
  show("dev_prompting", "next_turn", { turns: [{ turn: 2, code: "print('result')", feedback: "이번 실행 피드백" }] });
  expect(screen.getByText("print('result')")).toBeTruthy();
  expect(screen.getByText(/이번 실행 피드백/)).toBeTruthy();
  expect(screen.queryByText("평가 점수")).toBeNull();
});

it("shows public generated items while ignoring injected correctness fields", () => {
  show("rejection_eval", "generate", { items: [{ id: "a", text: "공개 설계 내용", explanation: "hidden solution" }] });
  expect(screen.getByText("공개 설계 내용")).toBeTruthy();
  expect(screen.queryByText("hidden solution")).toBeNull();
});

it("retrieves the saved CS report with cookies, without issuing another evaluation", async () => {
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "native", status: "graded",
    normalized_score: 72, total_score: 5, summary_report: "실제 저장 리포트", analysis_report: "분석", per_question: [] })));
  vi.stubGlobal("fetch", fetch);
  show("cs_eval", "create_session", { session_id: "native", status: "graded" });
  expect(await screen.findByText("실제 저장 리포트")).toBeTruthy();
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/cs-eval/sessions/native"), { credentials: "include", cache: "no-store" });
});

it("only follows allowlisted report routes on recovery", () => {
  const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
  show("test_design", "submit", { submitted: true }, "/api/admin/secret");
  expect(fetch).not.toHaveBeenCalled();
  expect(screen.getByText(/작업이 저장되었습니다/)).toBeTruthy();
});

it("renders a saved specification report through existing report components", () => {
  show("spec_design", "evaluate", { score: { total: 82, grade: "good", requirement_score: 80,
    decision_score: 85, consistency: 81, overengineering_penalty: 0, overengineered: [],
    weak_decisions: [], diverged_decisions: [], feedback: "실제 명세 피드백" },
    requirements: [], dimensions: [], overengineering: [] });
  expect(screen.getByText("실제 명세 피드백")).toBeTruthy();
  expect(screen.getByText("82")).toBeTruthy();
});

it("shows completed sample code runs", () => {
  show("coding_test", "run", { results: [{ index: 0, passed: true }] });
  expect(screen.getByText("샘플 결과: 1/1 통과")).toBeTruthy();
});

it("retrieves the saved final code judgement", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "graded",
    test_passed: 4, test_total: 5, strengths: [], weaknesses: [], analysis_report: "실제 코드 분석" }))));
  show("coding_test", "create_submission", { submission_id: "submission" });
  expect(await screen.findByText("실제 코드 분석")).toBeTruthy();
});

it("shows extracted rows without inventing correctness feedback", () => {
  show("office_prompting", "run", { predicted_rows: [{ record: "이번 추출 행" }] });
  expect(screen.getByText("이번 추출 행")).toBeTruthy();
  expect(screen.queryByText("F1")).toBeNull();
});

it("shows the stored office score only at scoring", () => {
  show("office_prompting", "score", { f1: 0.8, problems: [{ problem_index: 0, title: "첫 문제", precision: 0.8, recall: 0.8 }] });
  expect(screen.getByText("F1")).toBeTruthy();
  expect(screen.getByText(/첫 문제: 정밀도 80%/)).toBeTruthy();
});

it("shows the saved rejection judge report", () => {
  show("rejection_eval", "score", { topics: [{ topic_index: 0, f1: 0.8, precision: 0.8, recall: 0.8, report: "실제 거부 판단 리포트" }] });
  expect(screen.getByText("실제 거부 판단 리포트")).toBeTruthy();
});

it("retrieves the existing test-design report by the allowlisted session path", async () => {
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ candidate_name: "체험", status: "scored",
    weighted_score: 0.8, recall: 0.8, precision: 0.8, problems: [] })));
  vi.stubGlobal("fetch", fetch);
  show("test_design", "submit", { submitted: true }, "/test-design/sessions/native/problems/0/submit");
  expect(await screen.findByText("체험 님의 결과")).toBeTruthy();
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/test-design/sessions/native/result"), { credentials: "include", cache: "no-store" });
});
