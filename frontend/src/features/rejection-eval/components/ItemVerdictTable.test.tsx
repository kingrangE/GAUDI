import { render, screen } from "@testing-library/react";

import type { ResultItem } from "../types";
import { ItemVerdictTable } from "./ItemVerdictTable";

function item(over: Partial<ResultItem>): ResultItem {
  return {
    id: "x",
    text: "decision",
    is_flawed: false,
    flaw_type: "none",
    in_requirements: true,
    flaw_source: "none",
    explanation: "...",
    flagged: false,
    outcome: "correct_accept",
    ...over,
  };
}

describe("ItemVerdictTable", () => {
  it("renders per-item outcome, ground truth, and flaw source", () => {
    const items = [
      item({ id: "a", text: "decision a", flagged: true, flaw_source: "injected", outcome: "caught" }),
      item({ id: "b", text: "decision b", flagged: false, flaw_source: "out_of_scope", outcome: "missed" }),
      item({ id: "c", text: "decision c", flagged: false, flaw_source: "none", outcome: "correct_accept" }),
    ];
    render(<ItemVerdictTable items={items} />);

    expect(screen.getByText("정확히 거부")).toBeTruthy();
    expect(screen.getByText("놓침")).toBeTruthy();
    expect(screen.getByText("정확히 수용")).toBeTruthy();
    expect(screen.getByText("잘못된 설계")).toBeTruthy();
    expect(screen.getByText("요구사항에 없음")).toBeTruthy();
    // ground-truth column shows "거부 대상" for the two flaws
    expect(screen.getAllByText("거부 대상").length).toBe(2);
  });
});
