import { afterEach, beforeEach, expect, it, vi } from "vitest";

const id = "b".repeat(32);
const owner = "c".repeat(32);
const envelope = { http_status: 201, body: { session_id: "native" } };
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

beforeEach(() => { vi.resetModules(); });
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });

it("shares state and result observation for concurrent consumers, then stops", async () => {
  vi.useFakeTimers();
  const fetch = vi.fn().mockResolvedValueOnce(response({ status: "running", completed_units: 2, total_units: 5 }))
    .mockResolvedValueOnce(response({ status: "completed" })).mockResolvedValueOnce(response(envelope));
  vi.stubGlobal("fetch", fetch);
  const tracking = await import("./tracking");
  const first = tracking.observe(id, owner);
  const second = tracking.observe(id, owner);
  await vi.advanceTimersByTimeAsync(0);
  expect(tracking.getSnapshot()[0].state?.completed_units).toBe(2);
  expect(tracking.getSnapshot()[0].result).toBeUndefined();
  await vi.advanceTimersByTimeAsync(1000);
  expect((await first).status).toBe(201);
  expect(await (await second).json()).toEqual(envelope.body);
  expect(tracking.getSnapshot()[0].result?.body).toEqual(envelope.body);
  await vi.advanceTimersByTimeAsync(10000);
  expect(fetch).toHaveBeenCalledTimes(3);
});

it("waits for result retrieval even after server status is completed", async () => {
  let resolve!: (value: Response) => void;
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response({ status: "completed" }))
    .mockReturnValueOnce(new Promise<Response>((done) => { resolve = done; })));
  const tracking = await import("./tracking");
  const pending = tracking.observe(id, owner);
  await vi.waitFor(() => expect(resolve).toBeTypeOf("function"));
  expect(tracking.getSnapshot()[0].result).toBeUndefined();
  resolve(response(envelope));
  await pending;
  expect(tracking.getSnapshot()[0].result).toBeTruthy();
});

it("reconnects to the same job after a network failure without a POST", async () => {
  const fetch = vi.fn().mockRejectedValueOnce(new TypeError("private network error"))
    .mockResolvedValueOnce(response({ status: "completed" })).mockResolvedValueOnce(response(envelope));
  vi.stubGlobal("fetch", fetch);
  const tracking = await import("./tracking");
  await expect(tracking.observe(id, owner)).rejects.toThrow("조회 연결");
  expect(tracking.getSnapshot()[0].error).toContain("다시 연결");
  expect(tracking.getSnapshot()[0].error).not.toContain("private");
  await tracking.observe(id, owner);
  expect(tracking.getSnapshot()[0].error).toBeUndefined();
  expect(fetch.mock.calls.every(([url]) => String(url).includes(`/jobs/${id}`))).toBe(true);
});

it("caller abort does not free server work or discard the observer result", async () => {
  vi.useFakeTimers();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response({ status: "running" }))
    .mockResolvedValueOnce(response({ status: "completed" })).mockResolvedValueOnce(response(envelope)));
  const tracking = await import("./tracking");
  const work = tracking.observe(id, owner);
  const controller = new AbortController();
  const aborted = expect(tracking.withSignal(work, controller.signal)).rejects.toMatchObject({ name: "AbortError" });
  controller.abort();
  await aborted;
  await vi.advanceTimersByTimeAsync(1000);
  await work;
  expect(tracking.getSnapshot()[0].result).toBeTruthy();
});

it.each([401, 404])("does not fetch a result after ownership/session rejection %s", async (status) => {
  const fetch = vi.fn().mockResolvedValueOnce(response({}, status));
  vi.stubGlobal("fetch", fetch);
  const tracking = await import("./tracking");
  expect((await tracking.observe(id, owner)).status).toBe(status);
  expect(tracking.getSnapshot()[0].result).toBeUndefined();
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("does not show an old owner's result after switching visitor", async () => {
  let resolve!: (value: Response) => void;
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response({ status: "completed" }))
    .mockReturnValueOnce(new Promise<Response>((done) => { resolve = done; })));
  const tracking = await import("./tracking");
  const pending = tracking.observe(id, owner);
  await vi.waitFor(() => expect(resolve).toBeTypeOf("function"));
  tracking.setOwner("other-owner");
  resolve(response(envelope));
  expect((await pending).status).toBe(401);
  expect(tracking.getSnapshot()).toEqual([]);
});

it("invalid results never become a live report", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response({ status: "completed" }))
    .mockResolvedValueOnce(response({ http_status: 500, body: { secret: "bad" } })));
  const tracking = await import("./tracking");
  await expect(tracking.observe(id, owner)).rejects.toThrow("조회 연결");
  expect(tracking.getSnapshot()[0].result).toBeUndefined();
});

it("preserves session expiry at the result endpoint for the original caller", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response({ status: "completed" }))
    .mockResolvedValueOnce(response({}, 401)));
  const tracking = await import("./tracking");
  expect((await tracking.observe(id, owner)).status).toBe(401);
  expect(tracking.getSnapshot()[0].result).toBeUndefined();
  expect(tracking.getSnapshot()[0].error).toContain("세션이 만료");
});
