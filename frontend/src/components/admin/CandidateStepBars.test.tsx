import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CandidateStepBars, type StepScore } from "./CandidateStepBars";

const FIVE_STEPS: StepScore[] = [
  { key: "context_engineering", label: "CTX", score: 82 },
  { key: "spec_design", label: "SPEC", score: 54 },
  { key: "rejection_eval", label: "REJ", score: 33 },
  { key: "test_design", label: "TEST", score: 90 },
  { key: "dev_prompting", label: "DEV", score: 71 },
];

describe("CandidateStepBars", () => {
  it("renders one row per step", () => {
    render(<CandidateStepBars steps={FIVE_STEPS} />);
    expect(screen.getByText("CTX")).toBeInTheDocument();
    expect(screen.getByText("SPEC")).toBeInTheDocument();
    expect(screen.getByText("REJ")).toBeInTheDocument();
    expect(screen.getByText("TEST")).toBeInTheDocument();
    expect(screen.getByText("DEV")).toBeInTheDocument();
  });

  it("shows rounded scores as numbers", () => {
    render(<CandidateStepBars steps={FIVE_STEPS} />);
    expect(screen.getByText("82")).toBeInTheDocument();
    expect(screen.getByText("54")).toBeInTheDocument();
    expect(screen.getByText("90")).toBeInTheDocument();
  });

  it("shows em dash for null (not-yet-attempted) scores", () => {
    const steps: StepScore[] = [
      { key: "context_engineering", label: "CTX", score: 72 },
      { key: "spec_design", label: "SPEC", score: null },
      { key: "rejection_eval", label: "REJ", score: null },
      { key: "test_design", label: "TEST", score: null },
      { key: "dev_prompting", label: "DEV", score: null },
    ];
    render(<CandidateStepBars steps={steps} />);
    const dashes = screen.getAllByText("—");
    expect(dashes).toHaveLength(4);
    expect(screen.getByText("72")).toBeInTheDocument();
  });

  it("shows all dashes when no attempt has been made", () => {
    const emptySteps: StepScore[] = FIVE_STEPS.map((s) => ({ ...s, score: null }));
    render(<CandidateStepBars steps={emptySteps} />);
    const dashes = screen.getAllByText("—");
    expect(dashes).toHaveLength(5);
  });

  it("rounds fractional scores", () => {
    const steps: StepScore[] = [
      { key: "context_engineering", label: "CTX", score: 72.7 },
      { key: "spec_design", label: "SPEC", score: 54.2 },
      { key: "rejection_eval", label: "REJ", score: null },
      { key: "test_design", label: "TEST", score: null },
      { key: "dev_prompting", label: "DEV", score: null },
    ];
    render(<CandidateStepBars steps={steps} />);
    expect(screen.getByText("73")).toBeInTheDocument();
    expect(screen.getByText("54")).toBeInTheDocument();
  });

  it("renders container with accessible aria-label", () => {
    render(<CandidateStepBars steps={FIVE_STEPS} />);
    const container = screen.getByLabelText("단계별 점수");
    expect(container).toBeInTheDocument();
  });

  it("renders empty without error when steps array is empty", () => {
    const { container } = render(<CandidateStepBars steps={[]} />);
    expect(container.firstChild).toBeInTheDocument();
  });
});
