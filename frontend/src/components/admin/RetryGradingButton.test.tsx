import { fireEvent, render, waitFor, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import { RetryGradingButton } from "./RetryGradingButton";

const refresh = vi.fn();
const retry = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));
vi.mock("@/features/mock_exam/api", () => ({ mockExamApi: { retryStep: (...args: unknown[]) => retry(...args) } }));

it("reports failed retry and allows a new retry", async () => {
  retry.mockRejectedValueOnce(new Error("offline"));
  render(<RetryGradingButton attemptId="a" featureKey="spec_design" />);
  fireEvent.click(screen.getByRole("button", { name: "저장된 답안 재채점" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("재채점하지 못했습니다");
  expect(screen.getByRole("button")).toBeEnabled();
  retry.mockResolvedValueOnce({ recorded: true });
  fireEvent.click(screen.getByRole("button"));
  await waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  expect(retry).toHaveBeenCalledWith("a", "spec_design");
});
