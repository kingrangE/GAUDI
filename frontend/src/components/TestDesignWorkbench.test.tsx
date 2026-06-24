import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { ProblemPublic } from "../lib/types";
import { TestDesignWorkbench } from "./TestDesignWorkbench";

const EXAM_PROBLEM: ProblemPublic = {
  index: 0,
  id: "cx-churn-radar",
  title: "CX 이탈 레이더",
  difficulty: "hard",
  spec: "이탈 예측 시나리오",
  provided_tests: ["기본 예측 성공"],
};

describe("TestDesignWorkbench — examMode", () => {
  it("hides the problem picker, renders ProblemView, and calls onExamSubmit with flaws", async () => {
    const onExamSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(
      <TestDesignWorkbench
        examMode
        examProblem={EXAM_PROBLEM}
        onExamSubmit={onExamSubmit}
      />,
    );

    // Picker must not be rendered in exam mode
    expect(screen.queryByRole("combobox", { name: "문제 선택" })).toBeNull();

    // ProblemView renders the problem title and spec
    expect(screen.getByText("CX 이탈 레이더")).toBeTruthy();
    expect(screen.getByText("이탈 예측 시나리오")).toBeTruthy();

    // Type a flaw and click submit — no score, no router.push
    await user.type(screen.getByLabelText("검증 항목 1"), "빈 입력 처리 누락");
    await user.click(screen.getByRole("button", { name: "제출" }));

    expect(onExamSubmit).toHaveBeenCalledOnce();
    expect(onExamSubmit).toHaveBeenCalledWith(["빈 입력 처리 누락"]);
  });
});
