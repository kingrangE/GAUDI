import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ResultResponse } from "@/lib/types";

import ResultPage from "./page";

vi.mock("next/navigation", () => ({
  useParams: () => ({ sessionId: "sess-1" }),
}));

const submitProblem = vi.fn();
const getResult = vi.fn();
vi.mock("@/lib/api", () => ({
  submitProblem: (sessionId: string, index: number, flaws: string[]) =>
    submitProblem(sessionId, index, flaws),
  getResult: (sessionId: string) => getResult(sessionId),
  pendingSubmissionKey: (sessionId: string) => `td:pending:${sessionId}`,
}));

const RESULT: ResultResponse = {
  session_id: "sess-1",
  candidate_name: "anonymous",
  status: "completed",
  recall: 0.5,
  precision: 0.5,
  weighted_score: 0.5,
  problems: [],
};

afterEach(() => {
  submitProblem.mockReset();
  getResult.mockReset();
  sessionStorage.clear();
});

describe("ResultPage", () => {
  it("grades the pending submission behind a circular indicator, then shows the result", async () => {
    sessionStorage.setItem("td:pending:sess-1", JSON.stringify({ index: 0, flaws: ["x"] }));
    let resolveSubmit: (v: unknown) => void = () => {};
    submitProblem.mockReturnValue(
      new Promise((res) => {
        resolveSubmit = res;
      }),
    );
    getResult.mockResolvedValue(RESULT);

    render(<ResultPage />);

    // circular indicator while grading is in progress
    expect(await screen.findByRole("status")).toBeTruthy();
    expect(screen.getByText("채점 중입니다…")).toBeTruthy();
    expect(submitProblem).toHaveBeenCalledWith("sess-1", 0, ["x"]);
    // the handed-off submission is consumed exactly once
    expect(sessionStorage.getItem("td:pending:sess-1")).toBeNull();

    resolveSubmit({ problem_index: 0, submitted: true });

    expect(await screen.findByText("평가 결과")).toBeTruthy();
  });

  it("loads the result directly when there is no pending submission", async () => {
    getResult.mockResolvedValue(RESULT);

    render(<ResultPage />);

    expect(await screen.findByText("평가 결과")).toBeTruthy();
    expect(submitProblem).not.toHaveBeenCalled();
  });
});
