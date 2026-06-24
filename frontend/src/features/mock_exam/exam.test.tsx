import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ExamController } from "./ExamController";

// Mock the API client.
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

// Stub each feature workspace with a button that fires its exam submit, so the
// controller's orchestration (advance → finish) can be driven without mounting
// the real feature UIs (those have their own tests).
vi.mock("../../../feature_context_engineering", () => ({
  Workspace: ({ onExamSubmit }: { onExamSubmit: (v: string) => Promise<void> }) => (
    <button onClick={() => void onExamSubmit("md")}>step-context</button>
  ),
}));
vi.mock("../../../feature_spec_design", () => ({
  Workbench: ({ onExamSubmit }: { onExamSubmit: (v: string) => Promise<void> }) => (
    <button onClick={() => void onExamSubmit("instr")}>step-spec</button>
  ),
}));
vi.mock("../../../feature_dev_prompting", () => ({
  Workspace: ({ onExamSubmit }: { onExamSubmit: (v: string[]) => Promise<void> }) => (
    <button onClick={() => void onExamSubmit(["p"])}>step-dev</button>
  ),
}));
vi.mock("@/features/rejection-eval/RejectionWorkbench", () => ({
  RejectionWorkbench: ({ onExamSubmit }: { onExamSubmit: (ids: string[]) => Promise<void> }) => (
    <button onClick={() => void onExamSubmit(["x"])}>step-rejection</button>
  ),
}));
vi.mock("@/components/TestDesignWorkbench", () => ({
  TestDesignWorkbench: ({ onExamSubmit }: { onExamSubmit: (f: string[]) => Promise<void> }) => (
    <button onClick={() => void onExamSubmit(["flaw"])}>step-test</button>
  ),
}));

import { mockExamApi } from "./api";

const FLOW = [
  "context_engineering",
  "spec_design",
  "rejection_eval",
  "test_design",
  "dev_prompting",
];

/* eslint-disable @typescript-eslint/no-explicit-any */
const api = mockExamApi as any;

beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
  api.getAttempt.mockRejectedValue(new Error("no stored attempt"));
  api.start.mockResolvedValue({
    attempt_id: "att1",
    flow: FLOW,
    current_step: "context_engineering",
    remaining_seconds: 3600,
  });
  api.getStepMaterial.mockImplementation((_id: string, feature_key: string) =>
    Promise.resolve({
      feature_key,
      material: { topic_index: 3, title: "t", description: "d", requirements: [], spec: "s" },
    }),
  );
  api.submitStep.mockImplementation((_id: string, feature_key: string) => {
    const idx = FLOW.indexOf(feature_key);
    return Promise.resolve({ recorded: true, next_step: FLOW[idx + 1] ?? null });
  });
  api.finish.mockResolvedValue({ completed: true });
});

describe("ExamController", () => {
  it("renders the intro screen with a start button", () => {
    render(<ExamController />);
    expect(screen.getByText("시험을 시작합니다")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "시험 시작" })).toBeInTheDocument();
  });

  it("starts the exam and shows the first step with the overall timer", async () => {
    render(<ExamController />);
    fireEvent.click(screen.getByRole("button", { name: "시험 시작" }));
    expect(await screen.findByText("step-context")).toBeInTheDocument();
    expect(screen.getByTestId("countdown")).toHaveTextContent("3600");
  });

  it("advances through all 5 steps, finishes, and shows NO score", async () => {
    render(<ExamController />);
    fireEvent.click(screen.getByRole("button", { name: "시험 시작" }));

    for (const label of ["step-context", "step-spec", "step-rejection", "step-test", "step-dev"]) {
      fireEvent.click(await screen.findByText(label));
    }

    expect(await screen.findByText("수고하셨습니다")).toBeInTheDocument();
    expect(api.finish).toHaveBeenCalledWith("att1");
    expect(document.body.textContent ?? "").not.toMatch(/\d+\s*점/);
    await waitFor(() => expect(api.submitStep).toHaveBeenCalledTimes(5));
  });
});
