import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { USER_CODES, clearUserCode, getUserCode } from "@/lib/accessCodes";

import { EntryGate } from "./EntryGate";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

afterEach(() => {
  push.mockClear();
  clearUserCode();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("EntryGate", () => {
  it("opens the public hub without an entry code after server session issuance", async () => {
    vi.stubEnv("NEXT_PUBLIC_DEMO_ENABLED", "true");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ session_id: "visitor", expires_at: "later" }),
    }));
    const user = userEvent.setup();
    render(<EntryGate />);
    await user.click(screen.getByRole("button", { name: "둘러보기" }));
    expect(push).toHaveBeenCalledWith("/user");
    expect(getUserCode()).toBeNull();
  });

  it("routes ADMIN to the admin console", async () => {
    const user = userEvent.setup();
    render(<EntryGate />);

    await user.type(screen.getByLabelText("입장 코드"), "ADMIN");
    await user.click(screen.getByRole("button", { name: "입장" }));

    expect(push).toHaveBeenCalledWith("/admin/login");
  });

  it("stores the user code and routes to the user hub", async () => {
    const user = userEvent.setup();
    render(<EntryGate />);

    await user.type(screen.getByLabelText("입장 코드"), USER_CODES[0]);
    await user.click(screen.getByRole("button", { name: "입장" }));

    expect(getUserCode()).toBe(USER_CODES[0]);
    expect(push).toHaveBeenCalledWith("/user");
  });

  it("shows an error and does not navigate on an invalid code", async () => {
    const user = userEvent.setup();
    render(<EntryGate />);

    await user.type(screen.getByLabelText("입장 코드"), "WRONG-CODE");
    await user.click(screen.getByRole("button", { name: "입장" }));

    expect(screen.getByRole("alert")).toHaveTextContent("유효하지 않은 코드입니다");
    expect(push).not.toHaveBeenCalled();
    expect(getUserCode()).toBeNull();
  });
});
