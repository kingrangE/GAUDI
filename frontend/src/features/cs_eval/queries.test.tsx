import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "./api";
import { pollInterval, useCreateSession, useSessionResult } from "./queries";
import type { SessionResult } from "./types";

vi.mock("./api");

function wrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

const graded: SessionResult = {
  id: "s1",
  candidate_id: "c",
  status: "graded",
  total_score: 3,
  normalized_score: 58,
  summary_report: "보완: 체이닝",
  analysis_report: "진단",
  per_question: [],
  error: null,
};

afterEach(() => vi.clearAllMocks());

describe("pollInterval", () => {
  it("stops once terminal, keeps polling otherwise", () => {
    expect(pollInterval("graded")).toBe(false);
    expect(pollInterval("failed")).toBe(false);
    expect(pollInterval("grading")).toBeTypeOf("number");
    expect(pollInterval(undefined)).toBeTypeOf("number");
  });
});

describe("useCreateSession", () => {
  it("posts answers and returns the session id", async () => {
    vi.mocked(api.createSession).mockResolvedValue({
      session_id: "s1",
      status: "grading",
    });

    const { result } = renderHook(() => useCreateSession("c"), { wrapper: wrapper() });
    act(() => result.current.mutate([{ question_id: "ds-hashmap", answer_text: "충돌" }]));

    await waitFor(() => expect(result.current.data?.session_id).toBe("s1"));
    expect(api.createSession).toHaveBeenCalledWith({
      candidate_id: "c",
      answers: [{ question_id: "ds-hashmap", answer_text: "충돌" }],
    });
  });
});

describe("useSessionResult", () => {
  it("polls a session to a graded result", async () => {
    vi.mocked(api.getSession).mockResolvedValue(graded);

    const { result } = renderHook(() => useSessionResult("s1"), { wrapper: wrapper() });

    await waitFor(() => expect(result.current.data?.status).toBe("graded"));
    expect(result.current.data?.normalized_score).toBe(58);
  });
});
