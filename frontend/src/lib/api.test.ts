import { afterEach, describe, expect, it, vi } from "vitest";

import { createSession, getResult, submitProblem } from "./api";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function mockFetch(body: unknown, ok = true, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => body,
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("api client", () => {
  it("createSession POSTs candidate_name", async () => {
    const fetchMock = mockFetch({ session_id: "s1", candidate_name: "길원", problems: [] });
    const res = await createSession("길원");
    expect(res.session_id).toBe("s1");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/test-design/sessions");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ candidate_name: "길원" });
  });

  it("submitProblem hits the indexed path with flaws", async () => {
    const fetchMock = mockFetch({ problem_index: 1, submitted: true });
    await submitProblem("s1", 1, ["a", "b"]);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/test-design/sessions/s1/problems/1/submit");
    expect(JSON.parse(init.body)).toEqual({ flaws: ["a", "b"] });
  });

  it("throws on a non-ok response", async () => {
    mockFetch({}, false, 404);
    await expect(getResult("nope")).rejects.toThrow();
  });
});
