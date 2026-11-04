import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./jobs", () => ({ queuedFetch: (url: string, init: RequestInit) => fetch(url, init) }));

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv("NEXT_PUBLIC_DEMO_ENABLED", "true");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

function response(body: unknown, status = 200) {
  return { ok: status < 400, status, json: async () => body };
}

describe("demo session client", () => {
  it("shares cookie issuance across concurrent calls and includes cookies on feature requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ session_id: "visitor" }));
    vi.stubGlobal("fetch", fetchMock);
    const { demoFetch } = await import("./session");
    await Promise.all([
      demoFetch("http://localhost:8000/api/cs-eval/questions"),
      demoFetch("http://localhost:8000/test-design/sessions", { method: "POST", body: "{}" }),
    ]);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[0]).toEqual([
      "http://localhost:8000/api/demo/session", { method: "POST", credentials: "include" },
    ]);
    expect(fetchMock.mock.calls[1][1].credentials).toBe("include");
    expect(fetchMock.mock.calls[2][1]).toEqual({
      method: "POST", body: "{}", credentials: "include",
    });
  });

  it("does not send feature work if session issuance fails and allows a later retry", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({}, 503))
      .mockResolvedValue(response({ session_id: "visitor" }));
    vi.stubGlobal("fetch", fetchMock);
    const { demoFetch } = await import("./session");
    await expect(demoFetch("/evaluate", { method: "POST" })).rejects.toThrow("세션");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await demoFetch("/evaluate", { method: "POST" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("reports expiry without replaying a potentially costly mutation", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ session_id: "visitor" }))
      .mockResolvedValueOnce(response({}, 401));
    vi.stubGlobal("fetch", fetchMock);
    const { demoFetch } = await import("./session");
    await expect(demoFetch("/evaluate", { method: "POST" })).rejects.toThrow("만료");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("preserves the existing client contract when demo mode is disabled", async () => {
    vi.stubEnv("NEXT_PUBLIC_DEMO_ENABLED", "false");
    const fetchMock = vi.fn().mockResolvedValue(response([]));
    vi.stubGlobal("fetch", fetchMock);
    const { demoFetch } = await import("./session");
    await demoFetch("/public");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith("/public");
  });
});

it.each([
  [429, "demo daily budget is exhausted", "예산"],
  [429, "demo queue is full; retry later", "요청이 많습니다"],
  [409, "this feature already has a demo attempt", "체험이 이미 시작"],
])("explains demo rejection %s without leaking backend policy internals", async (status, detail, expected) => {
  vi.stubGlobal("fetch", vi.fn()
    .mockResolvedValueOnce(response({ session_id: "visitor" }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail }), { status })));
  const { demoFetch } = await import("./session");
  await expect(demoFetch("/evaluate", { method: "POST" })).rejects.toThrow(expected);
});
