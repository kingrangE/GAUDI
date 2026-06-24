/**
 * Login-less entry gate.
 *
 * The first screen asks for an "entry code". `ADMIN` opens the admin console;
 * one of the user codes below opens the user hub. There is no real auth yet —
 * the entered user code is stashed in sessionStorage so the admin dashboard can
 * later attribute results to a candidate by code.
 */

export const ADMIN_CODE = "ADMIN";

/** Pre-shared user entry codes (ambiguous chars 0/O, 1/I/L avoided). */
export const USER_CODES = ["AY-7F3K9Q", "AY-4M8X2P", "AY-6B5T3R"] as const;

export type CodeKind = "admin" | "user" | "invalid";

/** Trim + uppercase so input is matched case-insensitively and whitespace-tolerantly. */
export function normalize(code: string): string {
  return code.trim().toUpperCase();
}

export function isAdminCode(code: string): boolean {
  return normalize(code) === ADMIN_CODE;
}

export function isUserCode(code: string): boolean {
  const normalized = normalize(code);
  return USER_CODES.some((c) => c === normalized);
}

/** Single decision used by the entry gate. */
export function classifyCode(code: string): CodeKind {
  if (isAdminCode(code)) return "admin";
  if (isUserCode(code)) return "user";
  return "invalid";
}

export const STORAGE_KEY = "andyou:userCode";

/** Remember which user code entered — used later for result attribution. */
export function setUserCode(code: string): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(STORAGE_KEY, normalize(code));
}

export function getUserCode(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(STORAGE_KEY);
}

export function clearUserCode(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(STORAGE_KEY);
}
