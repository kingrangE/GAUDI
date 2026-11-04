import { webcrypto } from "node:crypto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const id = "a".repeat(32);
const url = "http://localhost:8000/test-design/sessions";
const init = { method: "POST", body: JSON.stringify({ candidate_name: "visitor" }), credentials: "include" as const };

beforeEach(() => {
  vi.resetModules();
  localStorage.clear();
  vi.stubGlobal("crypto", webcrypto);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

describe("queued native requests", () => {
  it("waits through queued state and polls without another evaluation submission", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ job_id: id }, 202))
      .mockResolvedValueOnce(response({ status: "queued" }))
      .mockResolvedValueOnce(response({ status: "completed" }))
      .mockResolvedValueOnce(response({ http_status: 200, body: { ready: true } }));
    vi.stubGlobal("fetch", fetchMock);
    const { queuedFetch } = await import("./jobs");
    expect(await (await queuedFetch(url, init, "owner")).json()).toEqual({ ready: true });
    expect(fetchMock.mock.calls.filter(([target]) => target === url)).toHaveLength(1);
  });

  it("submits with an idempotency key, polls, then restores native status and JSON", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ job_id: id }, 202))
      .mockResolvedValueOnce(response({ status: "completed" }))
      .mockResolvedValueOnce(response({ http_status: 201, body: { session_id: "native" } }));
    vi.stubGlobal("fetch", fetchMock);
    const { queuedFetch } = await import("./jobs");
    const result = await queuedFetch(url, init, "owner");
    expect(result.status).toBe(201);
    expect(await result.json()).toEqual({ session_id: "native" });
    expect(fetchMock.mock.calls[0][1].headers.get("Idempotency-Key")).toBeTruthy();
    expect(fetchMock.mock.calls[1][0]).toBe(`http://localhost:8000/api/demo/jobs/${id}`);
    expect(localStorage.length).toBe(0);
  });

  it("reuses the original key when the acknowledgement is lost", async () => {
    const fetchMock = vi.fn().mockRejectedValueOnce(new TypeError("network lost"))
      .mockResolvedValueOnce(response({ job_id: id }, 202))
      .mockResolvedValueOnce(response({ status: "completed" }))
      .mockResolvedValueOnce(response({ http_status: 200, body: {} }));
    vi.stubGlobal("fetch", fetchMock);
    const first = await import("./jobs");
    await expect(first.queuedFetch(url, init, "owner")).rejects.toThrow("network lost");
    const key = fetchMock.mock.calls[0][1].headers.get("Idempotency-Key");
    vi.resetModules();
    const reloaded = await import("./jobs");
    await reloaded.queuedFetch(url, init, "owner");
    expect(fetchMock.mock.calls[1][1].headers.get("Idempotency-Key")).toBe(key);
    expect(Array.from({ length: localStorage.length }, (_, i) => localStorage.getItem(localStorage.key(i)!)).join()).not.toContain("candidate_name");
  });

  it("resumes an accepted job after a reload without another submission", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(response({ job_id: id }, 202))
      .mockRejectedValueOnce(new TypeError("poll disconnected"))
      .mockResolvedValueOnce(response({ status: "completed" }))
      .mockResolvedValueOnce(response({ http_status: 200, body: { ok: true } }));
    vi.stubGlobal("fetch", fetchMock);
    const first = await import("./jobs");
    await expect(first.queuedFetch(url, init, "owner")).rejects.toThrow("poll disconnected");
    vi.resetModules();
    const reloaded = await import("./jobs");
    await reloaded.queuedFetch(url, init, "owner");
    expect(fetchMock.mock.calls.filter(([target]) => target === url)).toHaveLength(1);
  });

  it("stops on terminal failure and preserves the native HTTP error class", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(response({ job_id: id }, 202))
      .mockResolvedValueOnce(response({ status: "failed", error_status: 409 }));
    vi.stubGlobal("fetch", fetchMock);
    const { queuedFetch } = await import("./jobs");
    expect((await queuedFetch(url, init, "owner")).status).toBe(409);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(localStorage.length).toBe(0);
  });

  it("returns an expired-session response without replaying evaluation", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(response({ job_id: id }, 202))
      .mockResolvedValueOnce(response({}, 401));
    vi.stubGlobal("fetch", fetchMock);
    const { queuedFetch } = await import("./jobs");
    expect((await queuedFetch(url, init, "owner")).status).toBe(401);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});

it.each([[429, "허용된 실행량"], [413, "입력이 너무 큽니다"]])(
  "explains execution-time policy rejection %s", async (status, message) => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(response({ job_id: id }, 202))
      .mockResolvedValueOnce(response({ status: "failed", error_status: status })));
    const { queuedFetch } = await import("./jobs");
    const result = await queuedFetch(url, init, "owner");
    expect(result.status).toBe(status);
    expect((await result.json()).detail).toContain(message);
  },
);
