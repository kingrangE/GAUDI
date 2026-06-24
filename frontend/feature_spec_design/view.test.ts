import { describe, expect, it } from "vitest";

import { makeDimension, makeRequirement, makeResult } from "./fixtures";
import {
  dimensionStatus,
  dimensionTone,
  dimensionsByScore,
  gradeMeta,
  headline,
  percent,
  qualityMeta,
  requirementsBySatisfaction,
} from "./view";

describe("gradeMeta / qualityMeta", () => {
  it("maps grades and qualities to labels + tones", () => {
    expect(gradeMeta("excellent")).toEqual({ label: "매우 우수", tone: "great" });
    expect(qualityMeta("good")).toEqual({ label: "좋음", tone: "great" });
    expect(qualityMeta("bad")).toEqual({ label: "위험", tone: "bad" });
    expect(qualityMeta("unspecified")).toEqual({ label: "미지정", tone: "warn" });
  });
});

describe("percent", () => {
  it("rounds a ratio", () => {
    expect(percent(2 / 3)).toBe("67%");
    expect(percent(1)).toBe("100%");
  });
});

describe("dimensionTone / dimensionStatus", () => {
  it("diverged -> warn/갈림 regardless of quality", () => {
    const d = makeDimension({ diverged: true, quality: "good" });
    expect(dimensionTone(d)).toBe("warn");
    expect(dimensionStatus(d)).toBe("갈림");
  });
  it("pinned bad -> bad/위험", () => {
    const d = makeDimension({ quality: "bad", quality_score: 0, score: 0 });
    expect(dimensionTone(d)).toBe("bad");
    expect(dimensionStatus(d)).toBe("위험");
  });
  it("pinned good -> great/좋음", () => {
    expect(dimensionStatus(makeDimension())).toBe("좋음");
  });
});

describe("sorting helpers", () => {
  it("dimensionsByScore puts worst score first", () => {
    const dims = [
      makeDimension({ key: "a", score: 1 }),
      makeDimension({ key: "b", score: 0 }),
      makeDimension({ key: "c", score: 0.5 }),
    ];
    expect(dimensionsByScore(dims).map((d) => d.key)).toEqual(["b", "c", "a"]);
  });
  it("requirementsBySatisfaction puts least-satisfied first", () => {
    const reqs = [
      makeRequirement({ id: "a", satisfaction: 1 }),
      makeRequirement({ id: "b", satisfaction: 0 }),
    ];
    expect(requirementsBySatisfaction(reqs).map((r) => r.id)).toEqual(["b", "a"]);
  });
});

describe("headline", () => {
  it("celebrates a clean run", () => {
    expect(headline(makeResult())).toContain("모두 충족");
  });
  it("counts failed requirements", () => {
    const result = makeResult({
      requirements: [
        makeRequirement({ id: "a", satisfaction: 1 }),
        makeRequirement({ id: "b", satisfaction: 0 }),
      ],
      score: {
        total: 50,
        requirement_score: 50,
        decision_score: 50,
        consistency: 80,
        grade: "fair",
        failed_requirements: ["b"],
        weak_decisions: [],
        diverged_decisions: [],
        feedback: "",
      },
    });
    expect(headline(result)).toContain("1개 미충족");
    expect(headline(result)).toContain("보통");
  });
});
