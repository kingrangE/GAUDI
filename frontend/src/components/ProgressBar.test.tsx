import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProgressBar } from "./ProgressBar";

describe("ProgressBar", () => {
  it("renders current/total and percentage", () => {
    render(<ProgressBar current={2} total={5} />);
    expect(screen.getByText(/진행 2 \/ 5/)).toBeTruthy();
    expect(screen.getByText("40%")).toBeTruthy();
  });
});

it("represents an unknown duration without inventing a percentage", () => {
  const { container } = render(<ProgressBar current={0} total={1} indeterminate label="실행 대기" />);
  expect(container.textContent).not.toContain("0%");
  const bar = screen.getByRole("progressbar", { name: "실행 대기" });
  expect(bar.hasAttribute("aria-valuenow")).toBe(false);
});

it("caps completed units at 99 until the saved result is ready", () => {
  render(<ProgressBar current={5} total={5} maxPercent={99} label="저장 확인" />);
  expect(screen.getByRole("progressbar", { name: "저장 확인" }).getAttribute("aria-valuenow")).toBe("99");
});
