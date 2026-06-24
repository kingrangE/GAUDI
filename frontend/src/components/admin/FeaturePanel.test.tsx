import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import type { FeatureResult } from "@/lib/adminApi";

import { FeaturePanel } from "./FeaturePanel";

// ---------- Mock data helpers ----------

function makeBase(feature_key: string, overrides?: Partial<{ normalized_score: number; summary: string | null }>) {
  return {
    feature_key,
    label: feature_key,
    normalized_score: overrides?.normalized_score ?? 72,
    summary: overrides?.summary !== undefined ? overrides.summary : "LLM이 생성한 요약입니다.",
  };
}

const contextFeature: FeatureResult = {
  ...makeBase("context_engineering"),
  feature_key: "context_engineering",
  raw_result: {
    total: 72,
    scored: 11,
    dimensions: [
      { key: "coverage", label: "커버리지", score: 8, weight: 3, available: 3 },
      { key: "alignment", label: "정렬도", score: 7, weight: 2, available: 2 },
    ],
    results: [
      { id: "r1", text: "프로젝트 목표가 명시되어 있다", category: "목표", covered: true, evidence: "첫 단락에서 명시됨" },
      { id: "r2", text: "기술 스택이 설명되어 있다", category: "기술", covered: false, evidence: undefined },
    ],
  },
};

const specFeature: FeatureResult = {
  ...makeBase("spec_design"),
  feature_key: "spec_design",
  raw_result: {
    total: 81,
    score: {
      total: 81,
      requirement_score: 75,
      decision_score: 85,
      grade: "B+",
      overengineering_penalty: 2,
      failed_requirements: ["REQ-003"],
      weak_decisions: ["DEC-002"],
      feedback: "전반적으로 양호하나 일부 결정이 불충분합니다.",
    },
    requirements: [
      { id: "req1", text: "사용자 인증 기능", satisfaction: 0.9, satisfied: true },
      { id: "req2", text: "데이터 영속성", satisfaction: 0.4, satisfied: false },
    ],
    dimensions: [
      { key: "d1", label: "아키텍처", top_value: 4, agreement: 0.85, quality: 0.78 },
    ],
  },
};

const rejectionFeature: FeatureResult = {
  ...makeBase("rejection_eval"),
  feature_key: "rejection_eval",
  raw_result: {
    f1: 0.67,
    precision: 0.75,
    recall: 0.60,
    items: [
      { id: "i1", text: "결함이 있는 요구사항 A", is_flawed: true, flaw_type: "inconsistency", outcome: "caught", flagged: true },
      { id: "i2", text: "정상 요구사항 B", is_flawed: false, outcome: "correct_accept", flagged: false },
      { id: "i3", text: "결함이 있는 요구사항 C", is_flawed: true, flaw_type: "ambiguity", outcome: "missed", flagged: false },
    ],
    report: "응시자는 불일치 결함을 잘 탐지했으나 모호성은 놓쳤습니다.",
  },
};

const testFeature: FeatureResult = {
  ...makeBase("test_design"),
  feature_key: "test_design",
  raw_result: {
    weighted_score: 88,
    recall: 0.85,
    precision: 0.90,
    mean_quality: 0.82,
    flaws: [
      { id: "f1", text: "결함 A: 경계값 없음", severity: "high", category: "경계값", found: true, quality: 0.9 },
      { id: "f2", text: "결함 B: 타임아웃 미처리", severity: "medium", category: "오류처리", found: false, quality: undefined },
    ],
    false_positives: [{ id: "fp1" }],
    report: "대부분의 심각한 결함을 탐지했습니다.",
  },
};

const devPromptingFeature: FeatureResult = {
  ...makeBase("dev_prompting"),
  feature_key: "dev_prompting",
  raw_result: {
    total: 0.73,
    solved: true,
    score: {
      total: 0.73,
      pass_score: 0.8,
      best_pass_rate: 1.0,
      solved_turn: 3,
    },
    turns: [
      { turn: 1, prompt: "첫 번째 프롬프트", code: "def solution():\n    pass", passed_count: 2, total: 5, solved: false, feedback: "기본 케이스 통과" },
      { turn: 2, prompt: "두 번째 프롬프트", code: "def solution(n):\n    return n * 2", passed_count: 3, total: 5, solved: false },
      { turn: 3, prompt: "세 번째 프롬프트", code: "def solution(n):\n    return n * n", passed_count: 5, total: 5, solved: true },
    ],
  },
};

// ---------- Tests ----------

describe("FeaturePanel — context_engineering", () => {
  it("shows the step label and normalized score badge", () => {
    render(<FeaturePanel feature={contextFeature} />);
    expect(screen.getByText(/컨텍스트 엔지니어링/i)).toBeInTheDocument();
    expect(screen.getByText("72점")).toBeInTheDocument();
  });

  it("renders summary text", () => {
    render(<FeaturePanel feature={contextFeature} />);
    expect(screen.getByText("LLM이 생성한 요약입니다.")).toBeInTheDocument();
  });

  it("renders criteria coverage table with covered/not badges", () => {
    render(<FeaturePanel feature={contextFeature} />);
    expect(screen.getByText("기준별 커버리지")).toBeInTheDocument();
    // "충족" appears in both the <th> header and a Badge — use getAllByText
    expect(screen.getAllByText("충족").length).toBeGreaterThan(0);
    expect(screen.getByText("미충족")).toBeInTheDocument();
  });

  it("renders dimensions table", () => {
    render(<FeaturePanel feature={contextFeature} />);
    expect(screen.getByText("차원별 점수")).toBeInTheDocument();
    expect(screen.getByText("커버리지")).toBeInTheDocument();
    expect(screen.getByText("정렬도")).toBeInTheDocument();
  });

  it("renders metric for covered criteria count", () => {
    render(<FeaturePanel feature={contextFeature} />);
    expect(screen.getByText("11/2")).toBeInTheDocument(); // scored/results.length
  });
});

describe("FeaturePanel — spec_design", () => {
  it("shows grade badge", () => {
    render(<FeaturePanel feature={specFeature} />);
    expect(screen.getByText("B+")).toBeInTheDocument();
  });

  it("shows overengineering penalty", () => {
    render(<FeaturePanel feature={specFeature} />);
    expect(screen.getByText(/과설계 페널티/)).toBeInTheDocument();
  });

  it("shows requirements table with satisfaction", () => {
    render(<FeaturePanel feature={specFeature} />);
    expect(screen.getByText("요구사항 충족도")).toBeInTheDocument();
    expect(screen.getByText("사용자 인증 기능")).toBeInTheDocument();
    expect(screen.getByText("90%")).toBeInTheDocument();
  });

  it("shows failed requirements as bad badges", () => {
    render(<FeaturePanel feature={specFeature} />);
    expect(screen.getByText("실패한 요구사항")).toBeInTheDocument();
    expect(screen.getByText("REQ-003")).toBeInTheDocument();
  });

  it("shows LLM feedback text", () => {
    render(<FeaturePanel feature={specFeature} />);
    expect(screen.getByText("LLM 피드백")).toBeInTheDocument();
    expect(screen.getByText(/전반적으로 양호하나/)).toBeInTheDocument();
  });
});

describe("FeaturePanel — rejection_eval", () => {
  it("shows F1 / Precision / Recall metrics", () => {
    render(<FeaturePanel feature={rejectionFeature} />);
    expect(screen.getByText("F1")).toBeInTheDocument();
    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(screen.getByText("Precision")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("Recall")).toBeInTheDocument();
    expect(screen.getByText("60%")).toBeInTheDocument();
  });

  it("renders outcome ledger with caught/missed badges", () => {
    render(<FeaturePanel feature={rejectionFeature} />);
    expect(screen.getByText("결과 원장")).toBeInTheDocument();
    expect(screen.getByText("탐지")).toBeInTheDocument();   // caught
    expect(screen.getByText("누락")).toBeInTheDocument();   // missed
    expect(screen.getByText("정상수용")).toBeInTheDocument(); // correct_accept
  });

  it("shows the LLM report", () => {
    render(<FeaturePanel feature={rejectionFeature} />);
    expect(screen.getByText(/불일치 결함을 잘 탐지했으나/)).toBeInTheDocument();
  });
});

describe("FeaturePanel — test_design", () => {
  it("shows all four metrics", () => {
    render(<FeaturePanel feature={testFeature} />);
    expect(screen.getByText("가중 점수")).toBeInTheDocument();
    expect(screen.getByText("88")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument(); // recall
    // "90%" appears in the Precision metric AND in a flaw quality cell — use getAllByText
    expect(screen.getAllByText("90%").length).toBeGreaterThan(0);
    expect(screen.getByText("82%")).toBeInTheDocument(); // mean_quality
  });

  it("renders flaw table with severity and found badges", () => {
    render(<FeaturePanel feature={testFeature} />);
    expect(screen.getByText("결함 목록")).toBeInTheDocument();
    const highBadge = screen.getByText("high");
    expect(highBadge).toBeInTheDocument();
    // found / missed
    const foundBadges = screen.getAllByText("탐지");
    expect(foundBadges.length).toBeGreaterThan(0);
  });

  it("shows false positive count when present", () => {
    render(<FeaturePanel feature={testFeature} />);
    // Text is split by a <strong> element, so check parts independently.
    expect(screen.getByText(/오탐지/)).toBeInTheDocument();
    expect(screen.getByText("1건")).toBeInTheDocument();
  });
});

describe("FeaturePanel — dev_prompting", () => {
  it("shows solved turn metric", () => {
    render(<FeaturePanel feature={devPromptingFeature} />);
    expect(screen.getByText("풀이 턴")).toBeInTheDocument();
    expect(screen.getByText("3번")).toBeInTheDocument();
  });

  it("renders per-turn summary items", () => {
    render(<FeaturePanel feature={devPromptingFeature} />);
    expect(screen.getByText("턴별 결과")).toBeInTheDocument();
    expect(screen.getByText("TURN 1")).toBeInTheDocument();
    // "TURN 3" appears in the turn row AND in the CodePanel meta — use getAllByText
    expect(screen.getAllByText("TURN 3").length).toBeGreaterThan(0);
  });

  it("renders submitted code in a dark CodePanel", () => {
    render(<FeaturePanel feature={devPromptingFeature} />);
    // CodePanel label
    expect(screen.getByText("제출 코드")).toBeInTheDocument();
    // code from the solved turn (turn 3)
    expect(screen.getByText(/def solution/)).toBeInTheDocument();
  });

  it("renders gracefully when raw_result is null", () => {
    const noRaw: FeatureResult = {
      feature_key: "dev_prompting",
      label: "개발 프롬프팅",
      normalized_score: 0,
      summary: null,
      raw_result: null,
    };
    render(<FeaturePanel feature={noRaw} />);
    expect(screen.getByText(/개발 프롬프팅/i)).toBeInTheDocument();
  });
});

// ---------- No raw hex assertion ----------

describe("no raw hex colors in new admin source files", () => {
  const ROOT = join(process.cwd(), "src");
  const files = [
    join(ROOT, "components/admin/FeaturePanel.tsx"),
    join(ROOT, "components/admin/CandidateStepBars.tsx"),
    join(ROOT, "app/admin/page.tsx"),
    join(ROOT, "app/admin/results/[attemptId]/page.tsx"),
    join(ROOT, "app/admin/page.module.css"),
    join(ROOT, "lib/adminApi.ts"),
  ];

  for (const filePath of files) {
    const shortName = filePath.split("/src/")[1];
    it(`${shortName} contains no raw hex color tokens`, () => {
      const content = readFileSync(filePath, "utf-8");
      // Matches `[#rrggbb]` patterns (Tailwind arbitrary hex)
      expect(content).not.toMatch(/\[#[0-9a-fA-F]/);
    });
  }
});
