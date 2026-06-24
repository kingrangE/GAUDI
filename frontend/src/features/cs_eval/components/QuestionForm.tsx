"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";

import { Badge, Button, Panel, SectionLabel } from "@/components/ui";

import type { AnswerInput, Question } from "../types";
import { CountdownTimer } from "./CountdownTimer";

const EXAM_SECONDS = 20 * 60;

type QuestionFormProps = {
  questions: Question[];
  onSubmit: (answers: AnswerInput[]) => void;
  isSubmitting: boolean;
};

/** The solve screen: one textarea per CS question, submitted together. */
export function QuestionForm({ questions, onSubmit, isSubmitting }: QuestionFormProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});

  function submit() {
    onSubmit(
      questions.map((q) => ({
        question_id: q.id,
        answer_text: answers[q.id] ?? "",
      })),
    );
  }

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <div>
          <SectionLabel>CS 심층 평가</SectionLabel>
          <h1 className="mt-1 text-2xl font-bold text-ink-900">서술형 문제</h1>
        </div>
        <CountdownTimer seconds={EXAM_SECONDS} />
      </header>
      <p className="text-sm text-ink-soft">
        아는 만큼만 정확히 적으세요. 모르면 솔직히 모른다고 답하는 편이, 아는 척 틀리는 것보다
        높게 평가됩니다.
      </p>

      {questions.map((q, i) => (
        <Panel key={q.id}>
          <div className="flex items-center gap-2">
            <Badge tone="brand">{q.domain}</Badge>
            <SectionLabel>문항 {i + 1}</SectionLabel>
          </div>
          <div className="prose prose-sm mt-2 max-w-none text-ink-900">
            <ReactMarkdown>{q.prompt_md}</ReactMarkdown>
          </div>
          <textarea
            aria-label={`${q.domain} 답변`}
            value={answers[q.id] ?? ""}
            onChange={(e) =>
              setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))
            }
            placeholder="여기에 답을 서술하세요…"
            className="mt-3 h-32 w-full resize-y rounded-md border border-line bg-paper px-3 py-2 text-sm text-ink-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300"
          />
        </Panel>
      ))}

      <div className="flex justify-end">
        <Button onClick={submit} disabled={isSubmitting}>
          {isSubmitting ? "채점 준비 중…" : "제출하기"}
        </Button>
      </div>
    </div>
  );
}
