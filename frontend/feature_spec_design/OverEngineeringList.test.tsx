import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { makeOverItem } from "./fixtures";
import { OverEngineeringList } from "./OverEngineeringList";

describe("OverEngineeringList", () => {
  it("lists out-of-scope features with prevalence", () => {
    const items = [
      makeOverItem({ label: "two_factor_auth", count: 8, prevalence: 0.8 }),
      makeOverItem({ label: "admin_dashboard", count: 7, prevalence: 0.7 }),
    ];
    render(<OverEngineeringList items={items} />);

    expect(screen.getByText(/요구사항 밖 과설계 \(2\)/)).toBeInTheDocument();
    expect(screen.getByText("two_factor_auth")).toBeInTheDocument();
    expect(screen.getByText("80% 등장")).toBeInTheDocument();
    expect(screen.getByText("admin_dashboard")).toBeInTheDocument();
  });

  it("renders nothing when there is no over-engineering", () => {
    const { container } = render(<OverEngineeringList items={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
