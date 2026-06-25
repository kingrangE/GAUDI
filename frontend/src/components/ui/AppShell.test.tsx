import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppShell } from "./AppShell";

let mockPathname = "/coding-test";

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

describe("AppShell", () => {
  beforeEach(() => {
    mockPathname = "/coding-test";
  });

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

  it("points the logo at the menu-selection hub (not the entry-code gate) on a feature route", () => {
    mockPathname = "/coding-test";
    render(
      <AppShell>
        <p>child content</p>
      </AppShell>,
    );
    expect(screen.getByRole("link", { name: /and·you/ })).toHaveAttribute("href", "/user");
  });

  it("points the logo at /admin while inside the admin area", () => {
    mockPathname = "/admin/results";
    render(
      <AppShell>
        <p>child content</p>
      </AppShell>,
    );
    expect(screen.getByRole("link", { name: /and·you/ })).toHaveAttribute("href", "/admin");
  });
});
