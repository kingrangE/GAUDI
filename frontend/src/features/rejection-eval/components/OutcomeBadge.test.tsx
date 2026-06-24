import { render, screen } from "@testing-library/react";

import type { Outcome } from "../types";
import { OUTCOME_META, OutcomeBadge } from "./OutcomeBadge";

describe("OutcomeBadge", () => {
  const outcomes = Object.keys(OUTCOME_META) as Outcome[];

  it.each(outcomes)("renders the label for outcome %s", (outcome) => {
    render(<OutcomeBadge outcome={outcome} />);
    const badge = screen.getByRole("status");
    expect(badge.textContent).toContain(OUTCOME_META[outcome].label);
  });

  it("maps caught to 정확히 거부", () => {
    render(<OutcomeBadge outcome="caught" />);
    expect(screen.getByText(/정확히 거부/)).toBeTruthy();
  });
});
