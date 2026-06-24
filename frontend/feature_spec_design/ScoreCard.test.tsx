import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { makeRequirement, makeResult } from "./fixtures";
import { ScoreCard } from "./ScoreCard";

describe("ScoreCard", () => {
  it("shows total, grade, the 3-axis breakdown and a clean headline", () => {
    render(<ScoreCard result={makeResult()} />);
    expect(screen.getAllByText("100").length).toBeGreaterThan(0);
    expect(screen.getByText("매우 우수")).toBeInTheDocument();
    expect(screen.getByText(/결정도 견고합니다/)).toBeInTheDocument(); // headline
    expect(screen.getByText(/요구사항 충족/)).toBeInTheDocument(); // axis label
    expect(screen.getByText(/결정 품질/)).toBeInTheDocument();
  });

  it("renders all three axis labels", () => {
    render(<ScoreCard result={makeResult()} />);
    expect(screen.getByText(/일관성/)).toBeInTheDocument();
  });

  it("reflects a failed-requirement run in score and headline", () => {
    const result = makeResult({
      total_score: 50,
      requirements: [
        makeRequirement({ id: "a", satisfaction: 1 }),
        makeRequirement({ id: "b", satisfaction: 0 }),
      ],
      score: {
        total: 50,
        requirement_score: 50,
        decision_score: 50,
        consistency: 80,
        grade: "fair",
        failed_requirements: ["이메일 인증 필요"],
        weak_decisions: [],
        diverged_decisions: [],
        feedback: "미충족 요구사항: 이메일 인증 필요.",
      },
    });
    render(<ScoreCard result={result} />);
    expect(screen.getAllByText("50").length).toBeGreaterThan(0);
    expect(screen.getByText("보통")).toBeInTheDocument();
    expect(screen.getByText(/1개 미충족/)).toBeInTheDocument();
  });
});
