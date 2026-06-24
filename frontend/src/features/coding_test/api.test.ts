import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "./api";

function mockFetch(body: unknown, ok = true, status = 200) {
  return vi.fn().mockResolvedValue({
    ok,
    status,
    statusText: ok ? "OK" : "Error",
    json: async () => body,
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("api", () => {
  it("getProblems hits the list endpoint", async () => {
    const f = mockFetch([{ id: "two-sum", title: "두 수의 합", difficulty: "easy" }]);
    vi.stubGlobal("fetch", f);

    const out = await api.getProblems();

    expect(out).toHaveLength(1);
    expect(f.mock.calls[0][0]).toBe("http://localhost:8000/api/coding-test/problems");
  });

  it("runCode POSTs the code body", async () => {
    const f = mockFetch({ results: [] });
    vi.stubGlobal("fetch", f);

    await api.runCode("two-sum", "x = 1");

    const [url, init] = f.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/coding-test/problems/two-sum/run");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ code: "x = 1" });
  });

  it("createSubmission POSTs the full payload", async () => {
    const f = mockFetch({ submission_id: "s1", status: "grading" });
    vi.stubGlobal("fetch", f);

    const out = await api.createSubmission({
      problem_id: "two-sum",
      candidate_id: "c",
      code: "x = 1",
    });

    expect(out.submission_id).toBe("s1");
    expect(JSON.parse(f.mock.calls[0][1].body)).toEqual({
      problem_id: "two-sum",
      candidate_id: "c",
      code: "x = 1",
    });
  });

  it("throws on a non-2xx response", async () => {
    vi.stubGlobal("fetch", mockFetch({}, false, 404));
    await expect(api.getProblem("nope")).rejects.toThrow(/404/);
  });
});
