import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SampleList } from "./SampleList";

describe("SampleList", () => {
  it("renders prose and a code well with language tag + code", () => {
    const samples = [
      {
        index: 0,
        content: "결정: FastAPI\n\n```python\ndef solution(nums):\n    return sum(nums)\n```",
      },
    ];
    const { container } = render(<SampleList samples={samples} />);

    expect(screen.getByText("python")).toBeInTheDocument(); // lang tag
    expect(screen.getByText("결정: FastAPI")).toBeInTheDocument(); // prose
    // code content is split across highlight token spans, so assert via textContent
    expect(container.textContent).toContain("def");
    expect(container.textContent).toContain("solution");
    expect(container.textContent).toContain("return");
  });

  it("renders nothing when there are no samples", () => {
    const { container } = render(<SampleList samples={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
