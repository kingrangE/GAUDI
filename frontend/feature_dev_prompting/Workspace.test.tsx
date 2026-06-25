import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { EvaluationResult, ProblemPublic } from "./types";
import { Workspace } from "./Workspace";

const problem: ProblemPublic = {
  id: "sum-array",
  title: "배열의 합",
  statement: "정수 리스트 nums의 합을 return 하세요.",
  constraints: "1 <= len(nums) <= 100000",
  entry_point: "solution",
  starter_code: "def solution(nums):\n    answer = 0\n    return answer\n",
  time_limit_sec: 2,
  examples: [{ args: [[1, 2, 3]], expected: 6 }],
  public_example_count: 1,
};

const solvedResult: EvaluationResult = {
  problem_id: "sum-array",
  solved: true,
  score: {
    total: 100,
    pass_score: 70,
    understanding_score: 30,
    best_pass_rate: 1,
    solved: true,
    solved_turn: 1,
  },
  turns: [
    {
      turn: 1,
      prompt: "배열의 합을 구해줘",
      code: "def solution(nums):\n    return sum(nums)",
      passed_count: 3,
      total: 3,
      solved: true,
      feedback: "",
      case_results: [
        { index: 0, hidden: false, passed: true, status: "pass", expected: "6", got: "6" },
        { index: 1, hidden: true, passed: true, status: "pass", expected: null, got: null },
        { index: 2, hidden: true, passed: true, status: "pass", expected: null, got: null },
      ],
    },
  ],
};

function jsonRes(data: unknown): Response {
  return { ok: true, json: async () => data } as unknown as Response;
}

function stubFetch(problemList: ProblemPublic[]) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: unknown) => {
      const u = String(url);
      if (u.endsWith("/evaluate")) return jsonRes(solvedResult);
      if (u.endsWith("/problems")) return jsonRes(problemList);
      return jsonRes(problem);
    }),
  );
}

describe("Workspace examMode", () => {
  beforeEach(() => stubFetch([problem, { ...problem, id: "coin-change", title: "동전 교환" }]));
  afterEach(() => vi.unstubAllGlobals());

  it("runs without submitting, then 제출 sends the accumulated prompts", async () => {
    const onExamSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(
      <Workspace
        problemId="sum-array"
        initialProblem={problem}
        examMode
        onExamSubmit={onExamSubmit}
      />,
    );

    // picker must be absent even though multiple problems are available
    expect(screen.queryByRole("combobox", { name: "문제 선택" })).toBeNull();

    // 실행: runs the judge and shows the agent's code — but does NOT submit.
    await user.type(screen.getByPlaceholderText(/지시하세요/), "배열의 합을 구해줘");
    await user.click(screen.getByRole("button", { name: "실행" }));

    const codeRegion = await screen.findByRole("region", { name: "에이전트 코드" });
    await waitFor(() => expect(codeRegion.textContent).toContain("return sum(nums)"));
    expect(onExamSubmit).not.toHaveBeenCalled();

    // 실행 alone shows no score and no test ledger yet.
    expect(screen.queryByText(/맞았습니다/)).toBeNull();
    expect(screen.queryByLabelText("채점 결과")).toBeNull();

    // 제출: hands the accumulated prompt list to the parent for hidden-case scoring.
    await user.click(screen.getByRole("button", { name: "제출" }));
    await waitFor(() => expect(onExamSubmit).toHaveBeenCalledWith(["배열의 합을 구해줘"]));
  });

  it("테스트 채점 reveals only the public cases (hidden stay reserved for 제출)", async () => {
    const onExamSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(
      <Workspace
        problemId="sum-array"
        initialProblem={problem}
        examMode
        onExamSubmit={onExamSubmit}
      />,
    );

    // 테스트 채점 is disabled until something has been run.
    expect(screen.getByRole("button", { name: "테스트 채점" })).toBeDisabled();

    await user.type(screen.getByPlaceholderText(/지시하세요/), "배열의 합을 구해줘");
    await user.click(screen.getByRole("button", { name: "실행" }));
    await screen.findByRole("region", { name: "에이전트 코드" });

    await user.click(screen.getByRole("button", { name: "테스트 채점" }));

    // solvedResult has 1 public + 2 hidden cases → public-only summary is 1/1,
    // and the hidden rows must never be rendered to the candidate.
    const ledger = await screen.findByLabelText("채점 결과");
    expect(ledger).toHaveTextContent("통과 1/1");
    expect(ledger.textContent).not.toContain("숨김");
    // the overall score stays hidden in exam mode
    expect(screen.queryByText(/맞았습니다/)).toBeNull();
    expect(onExamSubmit).not.toHaveBeenCalled();
  });
});

describe("Workspace", () => {
  beforeEach(() => stubFetch([problem]));
  afterEach(() => vi.unstubAllGlobals());

  it("starts with the function stub already filled into the code panel", () => {
    render(<Workspace problemId="sum-array" initialProblem={problem} />);
    expect(screen.getByText("배열의 합")).toBeInTheDocument();
    const codeRegion = screen.getByRole("region", { name: "에이전트 코드" });
    expect(codeRegion.textContent).toContain("def solution(nums):");
    expect(codeRegion.textContent).toContain("return answer");
    // visible input/output example box
    expect(screen.getByText("입출력 예")).toBeInTheDocument();
    expect(screen.getByText("nums = [1,2,3]")).toBeInTheDocument();
  });

  it("runs a prompt and renders the agent code plus the verdict", async () => {
    const user = userEvent.setup();
    render(<Workspace problemId="sum-array" initialProblem={problem} />);

    await user.type(screen.getByPlaceholderText(/지시하세요/), "배열의 합을 구해줘");
    await user.click(screen.getByRole("button", { name: "채점 실행" }));

    expect(await screen.findByText("통과 3/3")).toBeInTheDocument();
    expect(screen.getByText(/맞았습니다/)).toBeInTheDocument();
    const codeRegion = screen.getByRole("region", { name: "에이전트 코드" });
    expect(codeRegion.textContent).toContain("def solution(nums):");
    expect(codeRegion.textContent).toContain("return sum(nums)");
  });

  it("disables the run button until the textarea has content", () => {
    render(<Workspace problemId="sum-array" initialProblem={problem} />);
    expect(screen.getByRole("button", { name: "채점 실행" })).toBeDisabled();
  });

  it("shows a problem picker when multiple problems are available", async () => {
    stubFetch([problem, { ...problem, id: "coin-change", title: "동전 교환" }]);
    render(<Workspace problemId="sum-array" initialProblem={problem} />);

    const picker = await screen.findByRole("combobox", { name: "문제 선택" });
    expect(within(picker).getByRole("option", { name: "동전 교환" })).toBeInTheDocument();
  });
});
