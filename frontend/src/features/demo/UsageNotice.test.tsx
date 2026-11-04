import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { UsageNotice } from "./UsageNotice";
import { demoFetch, isDemoEnabled } from "./session";

vi.mock("./session", () => ({ demoFetch: vi.fn(), isDemoEnabled: vi.fn() }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });

it("explains optional use and distinguishes unused, active and finished features", async () => {
  vi.mocked(isDemoEnabled).mockReturnValue(true);
  vi.mocked(demoFetch).mockResolvedValue(new Response(JSON.stringify({ limited: true, features: [
    { feature: "coding_test", remaining: 1, state: "available" },
    { feature: "dev_prompting", remaining: 0, state: "active" },
    { feature: "spec_design", remaining: 0, state: "completed" },
  ] })));
  render(<UsageNotice />);
  expect(await screen.findByText(/모두 이용할 필요는 없습니다/)).toBeTruthy();
  expect(screen.getByText("코딩: 1회 가능")).toBeTruthy();
  expect(screen.getByText("개발 프롬프팅: 시작됨 · 이어서 진행")).toBeTruthy();
  expect(screen.getByText("명세 설계: 체험 종료")).toBeTruthy();
});

it("does not issue sessions in ordinary mode", () => {
  vi.mocked(isDemoEnabled).mockReturnValue(false);
  const { container } = render(<UsageNotice />);
  expect(container.textContent).toBe("");
  expect(demoFetch).not.toHaveBeenCalled();
});

it("reports a usage lookup failure", async () => {
  vi.mocked(isDemoEnabled).mockReturnValue(true);
  vi.mocked(demoFetch).mockRejectedValue(new Error("연결 실패"));
  render(<UsageNotice />);
  expect((await screen.findByRole("alert")).textContent).toBe("연결 실패");
});
