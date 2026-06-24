import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ResultProblem } from "../lib/types";
import { ProblemResultCard } from "./ProblemResultCard";

const problem: ResultProblem = {
  problem_index: 0,
  problem_id: "problem_001",
  title: "average",
  candidate_flaws: ["빈 리스트"],
  flaws: [
    {
      id: "f1",
      text: "빈 리스트면 ZeroDivisionError",
      severity: "high",
      category: "edge_case",
      found: true,
      quality: 2,
      matched_candidate_text: "빈 리스트",
    },
    {
      id: "f2",
      text: "타입 검증 없음",
      severity: "medium",
      category: "validation",
      found: false,
      quality: 0,
      matched_candidate_text: null,
    },
  ],
  false_positives: ["엉뚱한 지적"],
  recall: 0.5,
  precision: 0.5,
  mean_quality: 2,
  weighted_score: 0.6,
  report: "절반을 찾았습니다.",
};

describe("ProblemResultCard", () => {
  it("shows found and missed flaws, false positives, and the report", () => {
    render(<ProblemResultCard problem={problem} />);
    expect(screen.getByText(/빈 리스트면 ZeroDivisionError/)).toBeTruthy();
    expect(screen.getByText(/타입 검증 없음/)).toBeTruthy();
    expect(screen.getByText(/엉뚱한 지적/)).toBeTruthy();
    expect(screen.getByText("절반을 찾았습니다.")).toBeTruthy();
  });
});
