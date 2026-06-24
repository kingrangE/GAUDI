import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ExamController } from "./ExamController";

vi.mock("./api", () => ({
  mockExamApi: {
    start: vi.fn(),
    getAttempt: vi.fn(),
    getStepMaterial: vi.fn(),
    generateRejection: vi.fn(),
    submitStep: vi.fn(),
    finish: vi.fn(),
  },
}));

vi.mock("@/lib/accessCodes", () => ({ getUserCode: () => "AY-7F3K9Q" }));

vi.mock("@/features/cs_eval/components/CountdownTimer", () => ({
  CountdownTimer: ({ seconds }: { seconds: number }) => (
    <span data-testid="countdown">{seconds}</span>
  ),
}));

import { mockExamApi } from "./api";
// Cast through unknown to avoid variance mismatch — mocks are set up via vi.mock factory above.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const api = mockExamApi as unknown as Record<string, { mockResolvedValue: (v: any) => void; mockRejectedValue: (v: any) => void; mockImplementation: (fn: any) => void }>;

const FULL_FLOW = [
  "context_engineering",
  "spec_design",
  "rejection_eval",
  "test_design",
  "dev_prompting",
];

beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
  api.getAttempt.mockRejectedValue(new Error("no stored attempt"));
});

describe("ExamController", () => {
  it("renders the intro screen with a start button", () => {
    render(<ExamController />);
    expect(screen.getByText("시험을 시작합니다")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "시험 시작" })).toBeInTheDocument();
  });

  it("shows the countdown timer and first step after starting", async () => {
    api.start.mockResolvedValue({
      attempt_id: "abc123",
      flow: FULL_FLOW,
      current_step: "context_engineering",
      remaining_seconds: 3600,
    });
    api.getStepMaterial.mockResolvedValue({});

    render(<ExamController />);
    fireEvent.click(screen.getByRole("button", { name: "시험 시작" }));

    await waitFor(() => {
      expect(screen.getByTestId("countdown")).toBeInTheDocument();
      // The step heading h2 specifically shows the current step name
      expect(screen.getByRole("heading", { name: "컨텍스트 엔지니어링" })).toBeInTheDocument();
    });
    expect(screen.getByTestId("countdown").textContent).toBe("3600");
  });

  it("advances to the next step after submitting", async () => {
    api.start.mockResolvedValue({
      attempt_id: "abc123",
      flow: FULL_FLOW,
      current_step: "context_engineering",
      remaining_seconds: 3600,
    });
    api.getStepMaterial.mockResolvedValue({});
    api.submitStep.mockResolvedValue({ recorded: true, next_step: "spec_design" });

    render(<ExamController />);
    fireEvent.click(screen.getByRole("button", { name: "시험 시작" }));

    await waitFor(() => screen.getByRole("heading", { name: "컨텍스트 엔지니어링" }));

    fireEvent.click(screen.getByRole("button", { name: /제출하고 다음/ }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "사양 설계" })).toBeInTheDocument();
    });
    expect(api.submitStep).toHaveBeenCalledWith(
      "abc123",
      "context_engineering",
      expect.objectContaining({ claude_md: expect.any(String) }),
    );
  });

  it("shows completion screen with no numeric score after the last step", async () => {
    api.start.mockResolvedValue({
      attempt_id: "last-step",
      flow: ["dev_prompting"],
      current_step: "dev_prompting",
      remaining_seconds: 120,
    });
    api.getStepMaterial.mockResolvedValue({});
    api.submitStep.mockResolvedValue({ recorded: true, next_step: null });
    api.finish.mockResolvedValue({ completed: true });

    render(<ExamController />);
    fireEvent.click(screen.getByRole("button", { name: "시험 시작" }));

    await waitFor(() => screen.getByRole("heading", { name: "개발 프롬프팅" }));

    fireEvent.click(screen.getByRole("button", { name: /제출하고 다음/ }));

    await waitFor(() => {
      expect(screen.getByText("수고하셨습니다")).toBeInTheDocument();
    });
    // No numeric score displayed
    expect(screen.queryByText(/\d+점/)).not.toBeInTheDocument();
    expect(api.finish).toHaveBeenCalledWith("last-step");
  });
});
