import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RunResults } from "./RunResults";

const columns = ["customer_id", "name", "region"];
const rows = [
  { customer_id: "C001", name: "고객001", region: "Seoul" },
  { customer_id: "C002", name: "고객002", region: "Busan" },
];

describe("RunResults", () => {
  it("shows the returned rows but NO correctness indicators", () => {
    const { container } = render(<RunResults columns={columns} rows={rows} hasRun />);
    expect(screen.getByText("C001")).toBeInTheDocument();
    expect(screen.getByText("C002")).toBeInTheDocument();
    // correctness must stay hidden during runs
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/precision|recall|f1|정답|맞힘|correct/i);
  });

  it("prompts the candidate to run before any run exists", () => {
    render(<RunResults columns={columns} rows={[]} hasRun={false} />);
    expect(screen.getByText(/프롬프트를 실행하면/)).toBeInTheDocument();
  });
});
