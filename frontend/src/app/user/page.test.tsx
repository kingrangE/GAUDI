import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import UserHubPage from "./page";

describe("UserHubPage", () => {
  it("offers both entry points with the correct links", () => {
    render(<UserHubPage />);

    const practice = screen.getByRole("link", { name: /개별 연습/ });
    expect(practice).toHaveAttribute("href", "/user/practice");

    const exam = screen.getByRole("link", { name: /실전 모의고사/ });
    expect(exam).toHaveAttribute("href", "/user/exam");
  });

  it("marks 실전 모의고사 as not yet ready", () => {
    render(<UserHubPage />);
    const exam = screen.getByRole("link", { name: /실전 모의고사/ });
    expect(exam).toHaveAttribute("aria-disabled", "true");
    expect(exam).toHaveTextContent("준비 중");
  });
});
