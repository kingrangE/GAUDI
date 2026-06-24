import { afterEach, describe, expect, it } from "vitest";

import {
  USER_CODES,
  classifyCode,
  clearUserCode,
  getUserCode,
  isAdminCode,
  setUserCode,
} from "./accessCodes";

afterEach(() => {
  clearUserCode();
});

describe("classifyCode", () => {
  it("treats ADMIN as admin, case- and whitespace-insensitively", () => {
    expect(classifyCode("ADMIN")).toBe("admin");
    expect(classifyCode("admin")).toBe("admin");
    expect(classifyCode("  Admin  ")).toBe("admin");
    expect(isAdminCode("admin")).toBe(true);
  });

  it("treats each pre-shared user code as user", () => {
    for (const code of USER_CODES) {
      expect(classifyCode(code)).toBe("user");
      expect(classifyCode(code.toLowerCase())).toBe("user");
    }
  });

  it("rejects anything else", () => {
    expect(classifyCode("")).toBe("invalid");
    expect(classifyCode("nope")).toBe("invalid");
    expect(classifyCode("AY-0000000")).toBe("invalid");
  });
});

describe("USER_CODES", () => {
  it("provides exactly three distinct codes", () => {
    expect(USER_CODES).toHaveLength(3);
    expect(new Set(USER_CODES).size).toBe(3);
  });
});

describe("user code storage", () => {
  it("round-trips and clears the entered code (normalized)", () => {
    expect(getUserCode()).toBeNull();
    setUserCode("ay-7f3k9q");
    expect(getUserCode()).toBe("AY-7F3K9Q");
    clearUserCode();
    expect(getUserCode()).toBeNull();
  });
});
