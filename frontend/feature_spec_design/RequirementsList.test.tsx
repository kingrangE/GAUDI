import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { makeRequirement } from "./fixtures";
import { RequirementsList } from "./RequirementsList";

describe("RequirementsList", () => {
  it("shows met count, lists least-satisfied first, marks pass/fail", () => {
    const requirements = [
      makeRequirement({ id: "a", text: "회원가입 가능", satisfaction: 1 }),
      makeRequirement({ id: "email", text: "이메일 인증 필요", satisfaction: 0 }),
    ];
    render(<RequirementsList requirements={requirements} />);

    expect(screen.getByText(/요구사항 충족 \(1\/2\)/)).toBeInTheDocument();
    const rows = screen.getAllByRole("listitem");
    expect(rows[0]).toHaveTextContent("이메일 인증 필요"); // satisfaction 0 -> first
    expect(rows[0]).toHaveTextContent("✗");
    expect(rows[0]).toHaveTextContent("0/10");
    expect(rows[1]).toHaveTextContent("회원가입 가능");
    expect(rows[1]).toHaveTextContent("✓");
  });

  it("renders nothing without requirements", () => {
    const { container } = render(<RequirementsList requirements={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
