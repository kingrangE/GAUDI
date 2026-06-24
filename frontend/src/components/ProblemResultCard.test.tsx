import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ResultProblem } from "../lib/types";
import { ProblemResultCard } from "./ProblemResultCard";

const problem: ResultProblem = {
  problem_index: 0,
  problem_id: "problem_001",
  title: "프로필 이미지 업로드",
  difficulty: "easy",
  candidate_flaws: ["파일 크기 상한"],
  flaws: [
    {
      id: "f1",
      text: "파일 크기 상한이 없다",
      severity: "high",
      category: "validation",
      found: true,
      quality: 2,
      matched_candidate_text: "파일 크기 상한",
    },
    {
      id: "f2",
      text: "Content-Type 검증 없음",
      severity: "high",
      category: "security",
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
  it("shows found and missed items, false positives, difficulty, and the report", () => {
    render(<ProblemResultCard problem={problem} />);
    expect(screen.getByText("쉬움")).toBeTruthy();
    expect(screen.getByText(/파일 크기 상한이 없다/)).toBeTruthy();
    expect(screen.getByText(/Content-Type 검증 없음/)).toBeTruthy();
    expect(screen.getByText(/엉뚱한 지적/)).toBeTruthy();
    expect(screen.getByText("절반을 찾았습니다.")).toBeTruthy();
  });
});
