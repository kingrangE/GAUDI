import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ResultResponse } from "../lib/types";
import { ResultSummary } from "./ResultSummary";

const result: ResultResponse = {
  session_id: "s1",
  candidate_name: "길원",
  status: "completed",
  recall: 0.6667,
  precision: 0.5,
  weighted_score: 0.75,
  problems: [],
};

describe("ResultSummary", () => {
  it("renders the candidate name and rounded metrics", () => {
    render(<ResultSummary result={result} />);
    expect(screen.getByText("길원 님의 결과")).toBeTruthy();
    expect(screen.getByText("67%")).toBeTruthy();
    expect(screen.getByText("50%")).toBeTruthy();
    expect(screen.getByText("75%")).toBeTruthy();
  });
});
