import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { AttemptSummary } from "@/lib/adminApi";

import { ResultsTable } from "./ResultsTable";

function attempt(partial: Partial<AttemptSummary>): AttemptSummary {
  return {
    id: "a1",
    candidate_code: "AY-7F3K9Q",
    candidate_label: "응시자 A",
    status: "completed",
    overall_normalized: 70,
    started_at: "2026-06-25T10:00:00+00:00",
    completed_at: "2026-06-25T10:30:00+00:00",
    feature_count: 5,
    ...partial,
  };
}

describe("ResultsTable", () => {
  it("shows an empty state when there are no attempts", () => {
    render(<ResultsTable attempts={[]} />);
    expect(screen.getByText(/아직 모의고사 응시 결과가 없습니다/)).toBeInTheDocument();
  });

  it("renders one row per attempt with the candidate label and detail link", () => {
    render(
      <ResultsTable
        attempts={[
          attempt({ id: "a1", candidate_label: "응시자 A", overall_normalized: 90 }),
          attempt({ id: "a2", candidate_label: "응시자 B", overall_normalized: 60 }),
        ]}
      />,
    );
    const rows = screen.getAllByRole("row").slice(1); // drop header
    expect(rows).toHaveLength(2);
    // Default sort is score-desc, so 응시자 A (90) is first.
    expect(within(rows[0]).getByText("응시자 A")).toBeInTheDocument();
    const links = screen.getAllByRole("link", { name: "리포트 보기" });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "/admin/results/a1");
  });
});
