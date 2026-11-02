import { act, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { CountdownTimer } from "./CountdownTimer";

afterEach(() => vi.useRealTimers());

it("uses elapsed wall time and expires once", () => {
  vi.useFakeTimers();
  const expire = vi.fn();
  render(<CountdownTimer seconds={2} onExpire={expire} />);
  act(() => { vi.advanceTimersByTime(2000); });
  expect(screen.getByLabelText("남은 시간")).toHaveTextContent("00:00");
  expect(expire).toHaveBeenCalledTimes(1);
  act(() => { vi.advanceTimersByTime(5000); });
  expect(expire).toHaveBeenCalledTimes(1);
});
