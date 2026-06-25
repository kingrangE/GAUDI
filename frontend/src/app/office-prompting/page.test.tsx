import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { CreateSessionResponse } from "@/features/office-prompting/types";

import OfficePromptingPage from "./page";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const createSession = vi.fn();
vi.mock("@/features/office-prompting/api", () => ({
  createSession: (...args: unknown[]) => createSession(...args),
  runProblem: vi.fn(),
}));

const SESSION: CreateSessionResponse = {
  session_id: "sess-1",
  candidate_name: "익명",
  problems: [
    {
      index: 0,
      title: "가전 구매 고객",
      description: "조건을 만족하는 고객을 찾으세요.",
      target_entity: "customer_id",
      max_runs: 3,
    },
  ],
  datasets: [
    { name: "customers", columns: ["customer_id", "name"], rows: [] },
  ],
};

afterEach(() => {
  push.mockClear();
  createSession.mockReset();
});

describe("OfficePromptingPage", () => {
  it("auto-starts an anonymous session — no name prompt — and shows the problem", async () => {
    createSession.mockResolvedValue(SESSION);
    render(<OfficePromptingPage />);

    // the problem view appears without any name-entry step
    expect(await screen.findByText("가전 구매 고객")).toBeTruthy();
    expect(createSession).toHaveBeenCalledTimes(1);
    expect(createSession).toHaveBeenCalledWith();

    // the removed entry screen is gone
    expect(screen.queryByPlaceholderText("이름")).toBeNull();
    expect(screen.queryByRole("button", { name: "평가 시작" })).toBeNull();
  });

  it("shows an error when the session fails to start", async () => {
    createSession.mockRejectedValue(new Error("boom"));
    render(<OfficePromptingPage />);

    expect(
      await screen.findByText("세션을 시작하지 못했습니다. 백엔드가 실행 중인지 확인하세요."),
    ).toBeTruthy();
  });
});
