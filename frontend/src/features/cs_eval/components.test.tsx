import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { QuestionForm } from "./components/QuestionForm";
import { ResponseTypeBadge } from "./components/ResponseTypeBadge";
import { ResultView } from "./components/ResultView";
import type { Question, SessionResult } from "./types";

const QUESTIONS: Question[] = [
  { id: "ds-hashmap", domain: "자료구조", prompt_md: "해시 테이블?", ordinal: 0 },
  { id: "os-process-thread", domain: "OS", prompt_md: "프로세스?", ordinal: 1 },
];

const graded: SessionResult = {
  id: "s",
  candidate_id: "c",
  status: "graded",
  total_score: 3,
  normalized_score: 58,
  summary_report: "보완이 필요한 키워드: 체이닝",
  analysis_report: "핵심 자료구조 이해는 양호하나 일부 개념이 부족하다.",
  per_question: [
    {
      question_id: "ds-hashmap",
      domain: "자료구조",
      response_type: "partial",
      score: 2,
      matched_keywords: ["충돌"],
      missing_keywords: ["체이닝"],
      rationale: "일부만 짚음",
    },
    {
      question_id: "os-process-thread",
      domain: "OS",
      response_type: "honest_unknown",
      score: -2,
      matched_keywords: [],
      missing_keywords: ["주소 공간"],
      rationale: "모름 인정",
    },
  ],
  error: null,
};

describe("ResponseTypeBadge", () => {
  it("labels each rubric bucket", () => {
    const { rerender } = render(<ResponseTypeBadge type="honest_unknown" />);
    expect(screen.getByText("솔직한 모름")).toBeInTheDocument();
    rerender(<ResponseTypeBadge type="bluff_wrong" />);
    expect(screen.getByText("허세-오답")).toBeInTheDocument();
  });
});

describe("ResultView", () => {
  it("renders the score, both reports, badges and keyword chips", () => {
    render(<ResultView result={graded} />);
    expect(screen.getByText("58")).toBeInTheDocument();
    expect(screen.getByText(/보완이 필요한 키워드/)).toBeInTheDocument();
    expect(screen.getByText(/핵심 자료구조 이해는/)).toBeInTheDocument();
    expect(screen.getByText("부분")).toBeInTheDocument();
    expect(screen.getByText("솔직한 모름")).toBeInTheDocument();
    expect(screen.getByText("충돌")).toBeInTheDocument();
    expect(screen.getByText("체이닝")).toBeInTheDocument();
  });
});

describe("QuestionForm", () => {
  it("collects an answer per question and submits them together", async () => {
    const onSubmit = vi.fn();
    render(<QuestionForm questions={QUESTIONS} onSubmit={onSubmit} isSubmitting={false} />);

    await userEvent.type(screen.getByLabelText("자료구조 답변"), "충돌과 체이닝");
    await userEvent.click(screen.getByRole("button", { name: "제출하기" }));

    expect(onSubmit).toHaveBeenCalledWith([
      { question_id: "ds-hashmap", answer_text: "충돌과 체이닝" },
      { question_id: "os-process-thread", answer_text: "" },
    ]);
  });
});
