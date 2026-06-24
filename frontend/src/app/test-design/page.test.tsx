import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { CreateSessionResponse } from "@/lib/types";

import TestDesignPage from "./page";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const createSession = vi.fn();
vi.mock("@/lib/api", () => ({
  createSession: (name: string) => createSession(name),
  pendingSubmissionKey: (sessionId: string) => `td:pending:${sessionId}`,
}));

const SESSION: CreateSessionResponse = {
  session_id: "sess-1",
  candidate_name: "anonymous",
  problems: [
    { index: 0, id: "problem_001", title: "업로드", difficulty: "easy", spec: "업로드 시나리오", provided_tests: ["정상 업로드 성공"] },
    { index: 1, id: "problem_002", title: "회원가입", difficulty: "easy", spec: "회원가입 시나리오", provided_tests: ["정상 가입 성공"] },
    { index: 2, id: "problem_003", title: "환불", difficulty: "medium", spec: "환불 시나리오", provided_tests: ["정상 환불 생성"] },
    { index: 3, id: "problem_004", title: "페이지", difficulty: "medium", spec: "페이지 시나리오", provided_tests: ["첫 페이지 반환"] },
    { index: 4, id: "problem_005", title: "알림", difficulty: "hard", spec: "알림 시나리오", provided_tests: ["큐 적재"] },
    { index: 5, id: "problem_006", title: "재고", difficulty: "hard", spec: "재고 시나리오", provided_tests: ["정상 차감"] },
  ],
};

afterEach(() => {
  push.mockClear();
  createSession.mockReset();
  sessionStorage.clear();
});

describe("TestDesignPage", () => {
  it("groups problems by difficulty and switches the brief on selection", async () => {
    createSession.mockResolvedValue(SESSION);
    const user = userEvent.setup();
    render(<TestDesignPage />);

    // the session auto-starts (no name prompt) and the picker appears
    const picker = await screen.findByLabelText("문제 선택");
    expect(createSession).toHaveBeenCalledTimes(1);

    // three difficulty tiers as <optgroup>s
    const groups = picker.querySelectorAll("optgroup");
    expect([...groups].map((g) => g.label)).toEqual(["쉬움", "보통", "어려움"]);

    // first easy problem is shown by default, with its provided basic tests
    expect(screen.getByText("업로드 시나리오")).toBeTruthy();
    expect(screen.getByText("이미 구현된 기본 테스트")).toBeTruthy();
    expect(screen.getByText("정상 업로드 성공")).toBeTruthy();

    // selecting a hard problem swaps the brief
    await user.selectOptions(picker, "5");
    expect(screen.getByText("재고 시나리오")).toBeTruthy();
  });

  it("stashes the submission and routes straight to the result page", async () => {
    createSession.mockResolvedValue(SESSION);
    const user = userEvent.setup();
    render(<TestDesignPage />);

    await screen.findByLabelText("문제 선택");

    await user.type(screen.getByLabelText("검증 항목 1"), "파일 크기 상한 없음");
    await user.click(screen.getByRole("button", { name: "제출하고 결과 보기" }));

    // the pending submission is handed off for the result page to grade
    expect(JSON.parse(sessionStorage.getItem("td:pending:sess-1") ?? "{}")).toEqual({
      index: 0,
      flaws: ["파일 크기 상한 없음"],
    });
    expect(push).toHaveBeenCalledWith("/test-design/result/sess-1");
  });
});
