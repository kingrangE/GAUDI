"use client";

import { useRouter } from "next/navigation";

import { useCreateSession, useQuestions } from "../queries";
import { QuestionForm } from "./QuestionForm";

const CANDIDATE_ID = "anonymous";

/** Solve page entry: load questions, submit answers, route to the result page. */
export function CsEvalSolve() {
  const router = useRouter();
  const questions = useQuestions();
  const create = useCreateSession(CANDIDATE_ID);

  if (questions.isPending) return <p className="text-ink-soft">불러오는 중…</p>;
  if (questions.isError || !questions.data) {
    return <p className="text-bad-600">문항을 불러오지 못했습니다.</p>;
  }

  return (
    <QuestionForm
      questions={questions.data}
      isSubmitting={create.isPending}
      onSubmit={(answers) =>
        create.mutate(answers, {
          onSuccess: (res) => router.push(`/cs-eval/${res.session_id}/result`),
        })
      }
    />
  );
}
