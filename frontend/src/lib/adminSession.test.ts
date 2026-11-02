// @vitest-environment node
import { describe, expect, it } from "vitest";

import { createAdminSession, validAdminSession } from "./adminSession";

const secret = "a-long-test-admin-secret";

describe("admin sessions", () => {
  it("accepts a signed session until it expires", async () => {
    const session = await createAdminSession(secret, 1000);
    expect(await validAdminSession(session, secret, 2000)).toBe(true);
    expect(await validAdminSession(session, secret, 9 * 60 * 60 * 1000)).toBe(false);
  });
  it("denies missing configuration, missing cookies and forged signatures", async () => {
    const session = await createAdminSession(secret);
    expect(await validAdminSession(session, undefined)).toBe(false);
    expect(await validAdminSession(undefined, secret)).toBe(false);
    expect(await validAdminSession(session, "wrong-secret")).toBe(false);
    expect(await validAdminSession("9999999999." + "0".repeat(64), secret)).toBe(false);
  });
});
