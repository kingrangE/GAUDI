import { afterEach, describe, expect, it, vi } from "vitest";

import { createSession, runProblem, scoreSession } from "./api";

function mockFetch(payload: unknown, ok = true, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("office-prompting api", () => {
  it("createSession POSTs the candidate name to the sessions endpoint", async () => {
    const fetchMock = mockFetch({ session_id: "s1" });
    await createSession("민수");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/office-prompting/sessions");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ candidate_name: "민수" });
  });

  it("runProblem hits the per-problem run endpoint with the prompt", async () => {
    const fetchMock = mockFetch({ problem_index: 0, predicted_ids: [], predicted_rows: [] });
    await runProblem("s1", 2, "조건");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/office-prompting/sessions/s1/problems/2/run");
    expect(JSON.parse(init.body)).toEqual({ prompt: "조건" });
  });

  it("scoreSession returns the parsed result", async () => {
    mockFetch({ session_id: "s1", f1: 1, total_correct: 3 });
    const res = await scoreSession("s1");
    expect(res.total_correct).toBe(3);
  });

  it("throws on a non-ok response", async () => {
    mockFetch({}, false, 409);
    await expect(scoreSession("s1")).rejects.toThrow(/409/);
  });
});
