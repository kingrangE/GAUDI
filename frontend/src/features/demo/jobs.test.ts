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
    expect(Object.keys(localStorage).filter((key) => key.startsWith("gaudi:pending-job:"))).toHaveLength(0);
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
    await expect(first.queuedFetch(url, init, "owner")).rejects.toThrow("조회 연결");
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
    expect(Object.keys(localStorage).filter((key) => key.startsWith("gaudi:pending-job:"))).toHaveLength(0);
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

it("recovers only this visitor's accepted IDs after reload without posting inputs", async () => {
  const owner = "b".repeat(32);
  localStorage.setItem(`gaudi:pending-job:${owner}:fingerprint`, JSON.stringify({ key: "key", jobId: id, path: "/spec-design/evaluate" }));
  localStorage.setItem("gaudi:pending-job:someone-else:fingerprint", JSON.stringify({ key: "other", jobId: "f".repeat(32) }));
  localStorage.setItem(`gaudi:pending-job:${owner}:unacknowledged`, JSON.stringify({ key: "lost-ack" }));
  const fetchMock = vi.fn().mockResolvedValueOnce(response({ status: "completed", feature: "spec_design" }))
    .mockResolvedValueOnce(response({ http_status: 200, body: { report: "restored" } }));
  vi.stubGlobal("fetch", fetchMock);
  const { recoverPending } = await import("./jobs");
  await recoverPending(owner);
  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(fetchMock.mock.calls.every(([url]) => String(url).includes(`/jobs/${id}`))).toBe(true);
  expect(localStorage.getItem(`gaudi:pending-job:${owner}:fingerprint`)).toBeNull();
  expect(localStorage.getItem(`gaudi:pending-job:${owner}:unacknowledged`)).not.toBeNull();
  expect(localStorage.getItem("gaudi:pending-job:someone-else:fingerprint")).not.toBeNull();
});

it("reuses a prepared practice session after reload instead of creating another resource", async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(response({ job_id: id }, 202))
    .mockResolvedValueOnce(response({ status: "completed", feature: "test_design", action: "create_session" }))
    .mockResolvedValueOnce(response({ http_status: 201, body: { session_id: "native" } }))
    .mockResolvedValueOnce(response({ status: "completed", feature: "test_design", action: "create_session" }))
    .mockResolvedValueOnce(response({ http_status: 201, body: { session_id: "native" } }));
  vi.stubGlobal("fetch", fetchMock);
  const first = await import("./jobs");
  await first.queuedFetch(url, init, "owner");
  vi.resetModules();
  const reloaded = await import("./jobs");
  const saved = await reloaded.queuedFetch(url, init, "owner");
  expect(await saved.json()).toEqual({ session_id: "native" });
  expect(fetchMock.mock.calls.filter(([target]) => target === url)).toHaveLength(1);
  expect(Array.from({ length: localStorage.length }, (_, i) => localStorage.getItem(localStorage.key(i)!)).join()).not.toContain("candidate_name");
});

it("does not let a late acknowledgement switch back to an earlier visitor", async () => {
  let acknowledge!: (response: Response) => void;
  const fetchMock = vi.fn().mockReturnValueOnce(new Promise<Response>((done) => { acknowledge = done; }));
  vi.stubGlobal("fetch", fetchMock);
  const { queuedFetch } = await import("./jobs");
  const tracking = await import("./tracking");
  const original = queuedFetch(url, init, "earlier-owner");
  await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  tracking.setOwner("current-owner");
  acknowledge(response({ job_id: id }, 202));
  expect((await original).status).toBe(401);
  expect(tracking.getOwner()).toBe("current-owner");
  expect(fetchMock).toHaveBeenCalledTimes(1);
});
