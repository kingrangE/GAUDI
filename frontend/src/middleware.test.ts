// @vitest-environment node
import { NextRequest } from "next/server";
import { afterEach, expect, it, vi } from "vitest";

import { ADMIN_COOKIE, createAdminSession } from "./lib/adminSession";
import { middleware } from "./middleware";

afterEach(() => vi.unstubAllEnvs());

it("protects direct admin URLs and lets the login page render", async () => {
  vi.stubEnv("ADMIN_TOKEN", "secret");
  for (const path of ["/admin", "/admin/results", "/admin/results/private-attempt"]) {
    const response = await middleware(new NextRequest(`https://gaudi.test${path}`));
    expect(response.headers.get("location")).toBe("https://gaudi.test/admin/login");
  }
  expect((await middleware(new NextRequest("https://gaudi.test/admin/login"))).status).toBe(200);
});

it("accepts a valid session and rejects it when configuration is removed", async () => {
  vi.stubEnv("ADMIN_TOKEN", "secret");
  const session = await createAdminSession("secret");
  const request = new NextRequest("https://gaudi.test/admin", {
    headers: { cookie: `${ADMIN_COOKIE}=${session}` },
  });
  expect((await middleware(request)).status).toBe(200);
  vi.stubEnv("ADMIN_TOKEN", "");
  expect((await middleware(request)).status).toBe(307);
});
