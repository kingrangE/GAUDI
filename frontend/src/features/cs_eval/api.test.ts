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
  it("getQuestions hits the list endpoint", async () => {
    const f = mockFetch([{ id: "ds-hashmap", domain: "자료구조", prompt_md: "?", ordinal: 0 }]);
    vi.stubGlobal("fetch", f);

    const out = await api.getQuestions();

    expect(out).toHaveLength(1);
    expect(f.mock.calls[0][0]).toBe("http://localhost:8000/api/cs-eval/questions");
  });

  it("createSession POSTs candidate_id + answers", async () => {
    const f = mockFetch({ session_id: "s1", status: "grading" });
    vi.stubGlobal("fetch", f);

    const out = await api.createSession({
      candidate_id: "c",
      answers: [{ question_id: "ds-hashmap", answer_text: "충돌" }],
    });

    expect(out.session_id).toBe("s1");
    const [url, init] = f.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/cs-eval/sessions");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({
      candidate_id: "c",
      answers: [{ question_id: "ds-hashmap", answer_text: "충돌" }],
    });
  });

  it("getSession hits the session endpoint", async () => {
    const f = mockFetch({ id: "s1", status: "graded" });
    vi.stubGlobal("fetch", f);

    await api.getSession("s1");

    expect(f.mock.calls[0][0]).toBe("http://localhost:8000/api/cs-eval/sessions/s1");
  });

  it("throws on a non-2xx response", async () => {
    vi.stubGlobal("fetch", mockFetch({}, false, 404));
    await expect(api.getSession("nope")).rejects.toThrow(/404/);
  });
});
