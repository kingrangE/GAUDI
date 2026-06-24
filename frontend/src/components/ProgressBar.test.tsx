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
