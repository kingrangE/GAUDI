import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchTasks, runEvaluation } from "./api";

function jsonRes(data: unknown, ok = true): Response {
  return { ok, status: ok ? 200 : 404, json: async () => data } as unknown as Response;
}

describe("api", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("fetchTasks GETs the tasks endpoint", async () => {
    const fetchMock = vi.fn(async () => jsonRes([{ id: "x" }]));
    vi.stubGlobal("fetch", fetchMock);

    expect(await fetchTasks()).toEqual([{ id: "x" }]);
    const [url] = fetchMock.mock.calls[0] as unknown as [string];
    expect(String(url)).toContain("/spec-design/tasks");
  });

  it("runEvaluation POSTs task_id + instruction as JSON", async () => {
    const fetchMock = vi.fn(async () => jsonRes({ task_id: "login-signup" }));
    vi.stubGlobal("fetch", fetchMock);

    await runEvaluation("login-signup", "FastAPI");
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(String(url)).toContain("/spec-design/evaluate");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      task_id: "login-signup",
      instruction: "FastAPI",
    });
  });

  it("throws on a non-ok response", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonRes({}, false)));
    await expect(fetchTasks()).rejects.toThrow("요청 실패 (404)");
  });
});
