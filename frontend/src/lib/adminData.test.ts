import { describe, expect, it } from "vitest";

import {
  getCandidateResult,
  getHighRiskItems,
  getQueueCounts,
  getSessionProgress,
  getTrackDashboard,
  sortCandidateResults,
  type EvaluationQueueItem,
} from "./adminData";

const queue: EvaluationQueueItem[] = [
  {
    id: "EV-1",
    candidate: "A",
    track: "Prompting",
    status: "pending",
    score: null,
    submittedAt: "10:00",
    risk: "low",
  },
  {
    id: "EV-2",
    candidate: "B",
    track: "Spec",
    status: "flagged",
    score: 55,
    submittedAt: "10:05",
    risk: "high",
  },
  {
    id: "EV-3",
    candidate: "C",
    track: "Context",
    status: "done",
    score: 90,
    submittedAt: "10:10",
    risk: "medium",
  },
];

describe("admin dashboard data", () => {
  it("counts queue items by review status", () => {
    expect(getQueueCounts(queue)).toEqual({
      pending: 1,
      reviewing: 0,
      flagged: 1,
      done: 1,
    });
  });

  it("returns only high risk queue items", () => {
    expect(getHighRiskItems(queue)).toEqual([queue[1]]);
  });

  it("keeps empty queues renderable", () => {
    expect(getQueueCounts([])).toEqual({
      pending: 0,
      reviewing: 0,
      flagged: 0,
      done: 0,
    });
    expect(getHighRiskItems([])).toEqual([]);
  });

  it("calculates session progress without dividing by zero", () => {
    expect(getSessionProgress({ completed: 3, participants: 4 } as never)).toBe(75);
    expect(getSessionProgress({ completed: 0, participants: 0 } as never)).toBe(0);
  });

  it("finds candidate detail data by id", () => {
    expect(getCandidateResult("candidate-2")?.name).toBe("박서연");
    expect(getCandidateResult("missing")).toBeUndefined();
  });

  it("finds track dashboard data by id", () => {
    expect(getTrackDashboard("agent")?.shortName).toBe("Agent 개발");
  });

  it("sorts candidate reports by score and name", () => {
    const results = [
      { name: "이준호", totalScore: 64, completedAt: "14:49" },
      { name: "김도윤", totalScore: 76, completedAt: "15:20" },
      { name: "박서연", totalScore: 88, completedAt: "15:04" },
    ] as never;

    expect(sortCandidateResults(results, "score-desc").map((result) => result.name)).toEqual([
      "박서연",
      "김도윤",
      "이준호",
    ]);
    expect(sortCandidateResults(results, "score-asc").map((result) => result.name)).toEqual([
      "이준호",
      "김도윤",
      "박서연",
    ]);
    expect(sortCandidateResults(results, "time-desc").map((result) => result.name)).toEqual([
      "김도윤",
      "박서연",
      "이준호",
    ]);
    expect(sortCandidateResults(results, "time-asc").map((result) => result.name)).toEqual([
      "이준호",
      "박서연",
      "김도윤",
    ]);
  });
});
