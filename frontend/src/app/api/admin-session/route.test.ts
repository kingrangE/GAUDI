// @vitest-environment node
import { NextRequest } from "next/server";
import { afterEach, expect, it, vi } from "vitest";

import { DELETE, POST } from "./route";

function request(token: string, origin = "https://gaudi.test") {
  return new NextRequest("https://gaudi.test/api/admin-session", {
    method: "POST", headers: { origin }, body: new URLSearchParams({ token }),
  });
}
afterEach(() => vi.unstubAllEnvs());

it("sets an HttpOnly session only for a valid admin password", async () => {
  vi.stubEnv("ADMIN_TOKEN", "secret");
  const response = await POST(request("secret"));
  expect(response.headers.get("location")).toBe("https://gaudi.test/admin");
  expect(response.headers.get("set-cookie")).toContain("HttpOnly");
  expect(response.headers.get("set-cookie")).toContain("SameSite=strict");
  const denied = await POST(request("wrong"));
  expect(denied.headers.get("location")).toContain("/admin/login?error=1");
  expect(denied.headers.get("set-cookie")).toBeNull();
});
it("denies unconfigured login and cross-origin requests", async () => {
  vi.stubEnv("ADMIN_TOKEN", "");
  expect((await POST(request(""))).headers.get("set-cookie")).toBeNull();
  expect((await POST(request("secret", "https://attacker.test"))).status).toBe(403);
});
it("clears the session on same-origin logout", async () => {
  const response = await DELETE(request(""));
  expect(response.status).toBe(204);
  expect(response.headers.get("set-cookie")).toContain("Max-Age=0");
  expect((await DELETE(request("", "https://attacker.test"))).status).toBe(403);
});
