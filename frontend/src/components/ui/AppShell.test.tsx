import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "./AppShell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/coding-test",
}));

describe("AppShell", () => {
  it("renders the children and brand chrome on a feature route", () => {
    render(
      <AppShell>
        <p>child content</p>
      </AppShell>,
    );
    expect(screen.getByText("child content")).toBeInTheDocument();
    expect(screen.getByText("EVAL")).toBeInTheDocument();
  });

  it("no longer shows the top-right feature shortcut nav", () => {
    render(
      <AppShell>
        <p>child content</p>
      </AppShell>,
    );
    // The quick-link nav (코딩 테스트 / CS 심층 평가 / …) has been removed.
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.queryByText("CS 심층 평가")).not.toBeInTheDocument();
    expect(screen.queryByText("개발 프롬프팅")).not.toBeInTheDocument();
  });
});
