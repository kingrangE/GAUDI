import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "./api";
import { pollInterval, useSubmitAndPoll } from "./queries";
import type { SubmissionResult } from "./types";

vi.mock("./api");

function wrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

const gradedResult: SubmissionResult = {
  id: "s1",
  problem_id: "two-sum",
  candidate_id: "c",
  status: "graded",
  test_passed: 5,
  test_total: 5,
  strengths: ["해시맵"],
  weaknesses: [],
  analysis_report: "좋은 풀이",
  code_quality_score: 80,
  error: null,
};

afterEach(() => vi.clearAllMocks());

describe("pollInterval", () => {
  it("stops polling once terminal", () => {
    expect(pollInterval("graded")).toBe(false);
    expect(pollInterval("failed")).toBe(false);
  });

  it("keeps polling while grading or unknown", () => {
    expect(pollInterval("grading")).toBeTypeOf("number");
    expect(pollInterval(undefined)).toBeTypeOf("number");
  });
});

describe("useSubmitAndPoll", () => {
  it("submits, then polls to a graded result", async () => {
    vi.mocked(api.createSubmission).mockResolvedValue({
      submission_id: "s1",
      status: "grading",
    });
    vi.mocked(api.getSubmission).mockResolvedValue(gradedResult);

    const { result } = renderHook(() => useSubmitAndPoll("two-sum", "c"), {
      wrapper: wrapper(),
    });
    act(() => result.current.submit.mutate("code"));

    await waitFor(() => expect(result.current.result.data?.status).toBe("graded"));
    expect(result.current.result.data?.code_quality_score).toBe(80);
    expect(api.createSubmission).toHaveBeenCalledOnce();
  });

  it("surfaces a failed submission", async () => {
    vi.mocked(api.createSubmission).mockResolvedValue({
      submission_id: "s2",
      status: "grading",
    });
    vi.mocked(api.getSubmission).mockResolvedValue({
      ...gradedResult,
      id: "s2",
      status: "failed",
      error: "boom",
    });

    const { result } = renderHook(() => useSubmitAndPoll("two-sum", "c"), {
      wrapper: wrapper(),
    });
    act(() => result.current.submit.mutate("code"));

    await waitFor(() => expect(result.current.result.data?.status).toBe("failed"));
    expect(result.current.result.data?.error).toBe("boom");
  });
});
