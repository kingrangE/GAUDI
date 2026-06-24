import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "./api";
import { ProblemList } from "./components/ProblemList";
import { ResultCards } from "./components/ResultCards";
import { RunResults } from "./components/RunResults";
import type { SubmissionResult } from "./types";

vi.mock("./api");
vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

function renderWithClient(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

afterEach(() => vi.clearAllMocks());

const graded: SubmissionResult = {
  id: "s",
  problem_id: "p",
  candidate_id: "c",
  status: "graded",
  test_passed: 4,
  test_total: 5,
  strengths: ["해시맵 활용"],
  weaknesses: ["변수명 모호"],
  analysis_report: "핵심 자료구조를 잘 골랐다.",
  code_quality_score: 82,
  error: null,
};

describe("ProblemList", () => {
  it("renders fetched problems with deep links", async () => {
    vi.mocked(api.getProblems).mockResolvedValue([
      { id: "two-sum", title: "두 수의 합", difficulty: "easy" },
      { id: "valid-parentheses", title: "올바른 괄호", difficulty: "easy" },
    ]);

    renderWithClient(<ProblemList />);

    await waitFor(() => screen.getByText("두 수의 합"));
    expect(screen.getByText("두 수의 합").closest("a")).toHaveAttribute(
      "href",
      "/coding-test/two-sum",
    );
  });
});

describe("RunResults", () => {
  it("shows a running state while pending", () => {
    render(<RunResults isPending />);
    expect(screen.getByText(/실행 중/)).toBeInTheDocument();
  });

  it("summarizes sample pass/fail (no score)", () => {
    render(
      <RunResults
        isPending={false}
        data={{
          results: [
            { index: 0, passed: true, error: null },
            { index: 1, passed: false, error: "wrong_answer" },
          ],
        }}
      />,
    );
    expect(screen.getByText("샘플 결과: 1/2 통과")).toBeInTheDocument();
    expect(screen.getByText(/케이스 2: 실패 \(wrong_answer\)/)).toBeInTheDocument();
  });
});

describe("ResultCards", () => {
  it("shows a grading state while pending", () => {
    render(<ResultCards isPending />);
    expect(screen.getByText("채점 중…")).toBeInTheDocument();
  });

  it("renders score, quality, keyword chips and the analysis report", () => {
    render(<ResultCards result={graded} isPending={false} />);
    expect(screen.getByText("4/5")).toBeInTheDocument();
    expect(screen.getByText("82")).toBeInTheDocument();
    expect(screen.getByText("해시맵 활용")).toBeInTheDocument();
    expect(screen.getByText("변수명 모호")).toBeInTheDocument();
    expect(screen.getByText("핵심 자료구조를 잘 골랐다.")).toBeInTheDocument();
  });

  it("shows an error when the submission failed", () => {
    render(<ResultCards result={{ ...graded, status: "failed", error: "boom" }} isPending={false} />);
    expect(screen.getByText(/boom/)).toBeInTheDocument();
  });
});
