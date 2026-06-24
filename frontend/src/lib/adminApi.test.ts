import { afterEach, describe, expect, it, vi } from "vitest";

import {
  fetchCandidates,
  fetchExamResult,
  formatScore,
  formatTime,
  sortAttempts,
  statusLabel,
  type AttemptSummary,
} from "./adminApi";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function mockFetch(body: unknown, ok = true, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({ ok, status, json: async () => body });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function attempt(partial: Partial<AttemptSummary>): AttemptSummary {
  return {
    id: "a1",
    candidate_code: "AY-7F3K9Q",
    candidate_label: "응시자 A",
    status: "completed",
    overall_normalized: 70,
    started_at: "2026-06-25T10:00:00+00:00",
    completed_at: "2026-06-25T10:30:00+00:00",
    feature_count: 5,
    ...partial,
  };
}

describe("fetch helpers", () => {
  it("fetchCandidates hits the admin endpoint and returns the body", async () => {
    const fetchMock = mockFetch([{ code: "AY-7F3K9Q", label: "응시자 A", latest_attempt: null }]);
    const res = await fetchCandidates();
    expect(res).toHaveLength(1);
    expect(fetchMock.mock.calls[0][0]).toContain("/api/admin/candidates");
  });

  it("swallows backend errors into an empty list (demo resilience)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("ECONNREFUSED")));
    expect(await fetchCandidates()).toEqual([]);
  });

  it("fetchExamResult returns null on a 404", async () => {
    mockFetch({}, false, 404);
    expect(await fetchExamResult("missing")).toBeNull();
  });
});

describe("sortAttempts", () => {
  it("sorts by score descending and sinks null scores to the bottom", () => {
    const rows = [
      attempt({ id: "low", overall_normalized: 40 }),
      attempt({ id: "none", overall_normalized: null, status: "in_progress" }),
      attempt({ id: "high", overall_normalized: 90 }),
    ];
    expect(sortAttempts(rows, "score-desc").map((a) => a.id)).toEqual([
      "high",
      "low",
      "none",
    ]);
  });

  it("sorts by completion time ascending", () => {
    const rows = [
      attempt({ id: "late", completed_at: "2026-06-25T12:00:00+00:00" }),
      attempt({ id: "early", completed_at: "2026-06-25T09:00:00+00:00" }),
    ];
    expect(sortAttempts(rows, "time-asc").map((a) => a.id)).toEqual(["early", "late"]);
  });
});

describe("formatters", () => {
  it("formats score and a missing score", () => {
    expect(formatScore(70.4)).toBe("70");
    expect(formatScore(null)).toBe("—");
  });

  it("formats a missing time as an em dash", () => {
    expect(formatTime(null)).toBe("—");
  });

  it("maps status keys to Korean labels", () => {
    expect(statusLabel("completed")).toBe("완료");
    expect(statusLabel("in_progress")).toBe("진행 중");
  });
});
