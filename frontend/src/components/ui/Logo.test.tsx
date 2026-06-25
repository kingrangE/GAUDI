import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Logo } from "./Logo";

describe("Logo", () => {
  it("renders the GAUDI wordmark", () => {
    const { container } = render(<Logo />);
    // The accent letter is a separate node, so assert on the combined text.
    expect(container.textContent).toContain("GAUDI");
  });

  it("accepts a size without breaking", () => {
    const { container } = render(<Logo size="lg" />);
    expect(container.textContent).toContain("GAUDI");
  });
});
