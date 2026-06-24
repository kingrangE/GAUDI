import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SAMPLE_TASKS, makeResult } from "./fixtures";
import { Workbench } from "./Workbench";

function jsonRes(data: unknown, ok = true): Response {
  return { ok, status: ok ? 200 : 500, json: async () => data } as unknown as Response;
}

function stubFetch(tasksOk = true) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: unknown) => {
      const u = String(url);
      if (u.endsWith("/spec-design/tasks")) return jsonRes(SAMPLE_TASKS, tasksOk);
      if (u.endsWith("/spec-design/evaluate")) return jsonRes(makeResult());
      return jsonRes({});
    }),
  );
}

describe("Workbench", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loads tasks, evaluates an instruction, and renders the score", async () => {
    stubFetch();
    const user = userEvent.setup();
    render(<Workbench />);

    await user.click(await screen.findByText("로그인 / 회원가입 기능 구현"));
    expect(screen.getByText("로그인 회원가입 brief")).toBeInTheDocument();

    await user.type(screen.getByLabelText("지시 입력"), "FastAPI, PostgreSQL");
    await user.click(screen.getByRole("button", { name: "지시 평가" }));

    expect(await screen.findByText("매우 우수")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "요구사항 충족" })).toBeInTheDocument();
  });

  it("surfaces an error when task loading fails", async () => {
    stubFetch(false);
    render(<Workbench />);
    expect(await screen.findByRole("alert")).toHaveTextContent("과제를 불러오지 못했습니다");
  });

  it("exam mode: hides picker and result pane, calls onExamSubmit", async () => {
    stubFetch();
    const onExamSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(
      <Workbench
        examMode
        examTaskId="login-signup"
        onExamSubmit={onExamSubmit}
      />,
    );

    // Task picker must be absent
    expect(screen.queryByText("로그인 / 회원가입 기능 구현")).not.toBeInTheDocument();

    // Brief from the locked task must appear
    expect(await screen.findByText("로그인 회원가입 brief")).toBeInTheDocument();

    // Result pane must not be rendered
    expect(screen.queryByRole("region", { name: "평가 결과" })).not.toBeInTheDocument();

    // Submit routes to onExamSubmit, not internal evaluate
    await user.type(screen.getByLabelText("지시 입력"), "my instruction");
    await user.click(screen.getByRole("button", { name: "지시 평가" }));

    expect(onExamSubmit).toHaveBeenCalledWith("my instruction");
    // Score never appears
    expect(screen.queryByText("매우 우수")).not.toBeInTheDocument();
  });
});
