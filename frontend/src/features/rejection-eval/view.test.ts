import { describe, expect, it } from "vitest";

import {
  decisionLabel,
  flawSourceLabel,
  outcomeMeta,
  percent,
  shouldReject,
  verdictMeta,
} from "./view";

describe("verdictMeta", () => {
  it("grades F1 into 우수 / 보통 / 미흡", () => {
    expect(verdictMeta(0.9)).toEqual({ label: "우수", tone: "good" });
    expect(verdictMeta(0.8)).toEqual({ label: "우수", tone: "good" });
    expect(verdictMeta(0.6)).toEqual({ label: "보통", tone: "warn" });
    expect(verdictMeta(0.5)).toEqual({ label: "보통", tone: "warn" });
    expect(verdictMeta(0.3)).toEqual({ label: "미흡", tone: "bad" });
  });
});

describe("outcomeMeta", () => {
  it("maps each outcome to a label and tone", () => {
    expect(outcomeMeta("caught")).toEqual({ label: "정확히 거부", tone: "good" });
    expect(outcomeMeta("missed")).toEqual({ label: "놓침", tone: "bad" });
    expect(outcomeMeta("false_alarm")).toEqual({ label: "오탐", tone: "warn" });
    expect(outcomeMeta("correct_accept")).toEqual({ label: "정확히 수용", tone: "neutral" });
  });
});

describe("flawSourceLabel / shouldReject", () => {
  it("labels and flags flaw sources", () => {
    expect(flawSourceLabel("injected")).toBe("잘못된 설계");
    expect(flawSourceLabel("out_of_scope")).toBe("요구사항에 없음");
    expect(flawSourceLabel("none")).toBe("");
    expect(shouldReject("injected")).toBe(true);
    expect(shouldReject("out_of_scope")).toBe(true);
    expect(shouldReject("none")).toBe(false);
  });
});

describe("percent / decisionLabel", () => {
  it("formats percent and the candidate decision", () => {
    expect(percent(0.5)).toBe("50%");
    expect(percent(0.333)).toBe("33%");
    expect(decisionLabel(true)).toBe("거부");
    expect(decisionLabel(false)).toBe("수용");
  });
});
