"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";

import type { ProblemPublic } from "../lib/types";
import { FlawListInput } from "./FlawListInput";
import { ProblemView } from "./ProblemView";

interface TestDesignWorkbenchProps {
  // Practice mode (examMode falsy): caller controls problem selection and flaws state
  problem?: ProblemPublic;
  flaws?: string[];
  onFlawsChange?: (flaws: string[]) => void;
  /** Called on submit; caller is responsible for any navigation / session storage. */
  onSubmit?: () => void;

  // Exam mode: lock to one problem, manage own flaws state, no navigation
  examMode?: boolean;
  examProblem?: ProblemPublic;
  /** Called with cleaned (trimmed, non-empty) flaws when the candidate submits. */
  onExamSubmit?: (flaws: string[]) => Promise<void>;
}

/**
 * Reusable two-column workbench: ProblemView on the left, FlawListInput on
 * the right.
 *
 * Practice mode (default): the parent page owns problem selection and flaws
 * state; pass `problem`, `flaws`, `onFlawsChange`, and `onSubmit`.
 *
 * Exam mode (`examMode={true}`): the workbench owns its own flaws state and
 * calls `onExamSubmit` on submit — no picker, no score, no navigation.
 */
export function TestDesignWorkbench({
  problem,
  flaws: flawsProp,
  onFlawsChange,
  onSubmit,
  examMode = false,
  examProblem,
  onExamSubmit,
}: TestDesignWorkbenchProps) {
  // Exam mode manages its own flaw list; practice mode is fully controlled
  const [examFlaws, setExamFlaws] = useState<string[]>([""]);
  const [submitting, setSubmitting] = useState(false);

  const activeProblem = examMode ? examProblem : problem;
  const flaws = examMode ? examFlaws : (flawsProp ?? [""]);
  const setFlaws = examMode ? setExamFlaws : (onFlawsChange ?? (() => {}));

  const cleanedFlaws = flaws.map((f) => f.trim()).filter(Boolean);
  const canSubmit = cleanedFlaws.length > 0 && !submitting;

  async function handleSubmit() {
    if (!canSubmit) return;
    if (examMode && onExamSubmit) {
      setSubmitting(true);
      try {
        await onExamSubmit(cleanedFlaws);
      } finally {
        setSubmitting(false);
      }
    } else if (!examMode && onSubmit) {
      onSubmit();
    }
  }

  if (!activeProblem) return null;

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      {/* Left — the prose scenario to verify */}
      <Panel className="min-h-0 overflow-y-auto">
        <ProblemView problem={activeProblem} />
      </Panel>

      {/* Right — verification items */}
      <Panel className="flex min-h-0 flex-col">
        <SectionLabel>추가 검증 항목</SectionLabel>
        <p className="mt-2 text-xs leading-relaxed text-ink-soft">
          이미 구현된 기본 테스트 외에, 추가로 검증이 필요한 항목을 한 줄에 하나씩 설계하세요.
        </p>
        <div className="mt-3 min-h-0 flex-1 overflow-y-auto">
          <FlawListInput flaws={flaws} onChange={setFlaws} />
        </div>
        <div className="mt-4 flex items-center justify-end">
          <Button disabled={!canSubmit} onClick={() => void handleSubmit()}>
            {submitting ? "제출 중…" : examMode ? "제출" : "제출하고 결과 보기"}
          </Button>
        </div>
      </Panel>
    </div>
  );
}
