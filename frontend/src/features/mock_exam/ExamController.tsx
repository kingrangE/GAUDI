"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { CountdownTimer } from "@/features/cs_eval/components/CountdownTimer";
import { RejectionWorkbench } from "@/features/rejection-eval/RejectionWorkbench";
import type { PublicItem, TopicMeta } from "@/features/rejection-eval/types";
import { TestDesignWorkbench } from "@/components/TestDesignWorkbench";
import { getUserCode } from "@/lib/accessCodes";
import type { ProblemPublic } from "@/lib/types";

import { Workspace as ContextWorkspace } from "../../../feature_context_engineering";
import { Workspace as DevWorkspace } from "../../../feature_dev_prompting";
import { Workbench as SpecWorkbench } from "../../../feature_spec_design";

import { mockExamApi } from "./api";
import type { FeatureKey } from "./types";

const STEP_LABELS: Record<FeatureKey, string> = {
  context_engineering: "컨텍스트 엔지니어링",
  spec_design: "명세 설계",
  rejection_eval: "거부 능력",
  test_design: "테스트 설계",
  dev_prompting: "개발 프롬프팅",
};

// Themed content ids — the same content the practice screens show.
const CONTEXT_PROJECT_ID = "cx-churn-radar";
const SPEC_TASK_ID = "cx-churn-radar-topn";
const DEV_PROBLEM_ID = "churn-risk-stream";

const DEFAULT_FLOW: FeatureKey[] = [
  "context_engineering",
  "spec_design",
  "rejection_eval",
  "test_design",
  "dev_prompting",
];

const SESSION_KEY = "mockExam:attemptId";

type Phase = "intro" | "loading" | "exam" | "finishing" | "done";

interface StepMaterial {
  feature_key: FeatureKey;
  material: Record<string, unknown>;
}

export function ExamController() {
  const [phase, setPhase] = useState<Phase>("intro");
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [flow, setFlow] = useState<FeatureKey[]>(DEFAULT_FLOW);
  const [completedSteps, setCompletedSteps] = useState<FeatureKey[]>([]);
  const [currentStep, setCurrentStep] = useState<FeatureKey | null>(null);
  const [stepMaterial, setStepMaterial] = useState<StepMaterial | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [failedSteps, setFailedSteps] = useState<FeatureKey[]>([]);
  // In-flight background scoring requests. The user advances without awaiting
  // these; the final step waits for all of them before finalizing the score.
  const pendingRef = useRef<Promise<unknown>[]>([]);

  const loadMaterial = useCallback(async (id: string, step: FeatureKey) => {
    const m = (await mockExamApi.getStepMaterial(id, step)) as unknown as StepMaterial;
    setStepMaterial(m);
  }, []);

  // Restore an in-progress attempt on mount.
  useEffect(() => {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (!stored) return;
    mockExamApi
      .getAttempt(stored)
      .then(async (status) => {
        if (status.status === "finished" || status.status === "completed") {
          sessionStorage.removeItem(SESSION_KEY);
          return;
        }
        setAttemptId(stored);
        setFlow((status.flow as FeatureKey[]) ?? DEFAULT_FLOW);
        setCompletedSteps((status.completed_steps as FeatureKey[]) ?? []);
        setRemainingSeconds(status.remaining_seconds);
        if (status.remaining_seconds <= 0) {
          await mockExamApi.finish(stored);
          sessionStorage.removeItem(SESSION_KEY);
          setPhase("done");
          return;
        }
        const step = status.current_step as FeatureKey | null;
        setCurrentStep(step);
        if (step) await loadMaterial(stored, step);
        setPhase("exam");
      })
      .catch(() => sessionStorage.removeItem(SESSION_KEY));
  }, [loadMaterial]);

  const startExam = useCallback(async () => {
    setPhase("loading");
    setError(null);
    try {
      const code = getUserCode() ?? "ANON";
      const res = await mockExamApi.start(code);
      sessionStorage.setItem(SESSION_KEY, res.attempt_id);
      setAttemptId(res.attempt_id);
      setFlow((res.flow as FeatureKey[]) ?? DEFAULT_FLOW);
      setCompletedSteps([]);
      const step = res.current_step as FeatureKey;
      setCurrentStep(step);
      setRemainingSeconds(res.remaining_seconds);
      await loadMaterial(res.attempt_id, step);
      setPhase("exam");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("intro");
    }
  }, [loadMaterial]);

  // Submit the current step's input, then advance IMMEDIATELY — the server-side
  // LLM scoring is slow, so we fire it in the background instead of awaiting it.
  // The next step is derived from the locally-known `flow` (no need for the
  // server's `next_step`), so the candidate never waits between problems.
  const handleSubmit = useCallback(
    async (feature: FeatureKey, input: unknown) => {
      if (!attemptId) return;
      setError(null);

      // Fire scoring in the background. Swallow failures into `failedSteps` so a
      // single failed step can't reject the Promise.allSettled at finish time.
      const pending = mockExamApi.submitStep(attemptId, feature, input).catch(() => {
        setFailedSteps((prev) => (prev.includes(feature) ? prev : [...prev, feature]));
      });
      pendingRef.current.push(pending);

      setCompletedSteps((prev) => (prev.includes(feature) ? prev : [...prev, feature]));

      const idx = flow.indexOf(feature);
      const next = idx >= 0 && idx + 1 < flow.length ? flow[idx + 1] : null;

      if (!next) {
        // Last step: wait for every background scoring to land so finalize can
        // average a complete set of feature scores, then close out the exam.
        setPhase("finishing");
        await Promise.allSettled(pendingRef.current);
        pendingRef.current = [];
        await mockExamApi.finish(attemptId);
        sessionStorage.removeItem(SESSION_KEY);
        setPhase("done");
      } else {
        setCurrentStep(next);
        await loadMaterial(attemptId, next);
      }
    },
    [attemptId, flow, loadMaterial],
  );

  const generateRejection = useCallback(
    async (prompt: string): Promise<PublicItem[]> => {
      if (!attemptId) return [];
      const res = await mockExamApi.generateRejection(attemptId, prompt);
      return res.items as PublicItem[];
    },
    [attemptId],
  );

  // ---- Render ----

  if (phase === "intro") {
    return (
      <div className="flex min-h-[60vh] items-center justify-center py-10">
        <Panel className="w-full max-w-xl text-center">
          <SectionLabel>실전 모의고사</SectionLabel>
          <h1 className="mt-3 text-2xl font-bold tracking-tight text-ink-900">시험을 시작합니다</h1>
          <p className="mt-3 text-sm leading-relaxed text-ink-soft">
            cx-churn-radar 과제를 컨텍스트 → 명세 → 거부 → 테스트 → 개발 프롬프팅 순서로 진행합니다.
            <br />각 단계는 개별 연습과 동일한 화면입니다. 점수는 종료 후 관리자만 확인합니다.
          </p>
          {error && (
            <p className="mt-3 rounded border border-bad-100 bg-bad-50 px-3 py-2 text-sm text-bad-600">
              {error}
            </p>
          )}
          <div className="mt-6">
            <Button onClick={() => void startExam()}>시험 시작</Button>
          </div>
        </Panel>
      </div>
    );
  }

  if (phase === "loading") {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <span className="text-ink-soft">시험을 준비하는 중…</span>
      </div>
    );
  }

  if (phase === "finishing") {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <span className="text-ink-soft">제출을 채점하는 중…</span>
      </div>
    );
  }

  if (phase === "done") {
    return (
      <div className="flex min-h-[60vh] items-center justify-center py-10">
        <Panel className="w-full max-w-xl text-center">
          <SectionLabel>완료</SectionLabel>
          <h1 className="mt-3 text-2xl font-bold tracking-tight text-ink-900">수고하셨습니다</h1>
          <p className="mt-3 text-sm text-ink-soft">
            제출이 완료되었습니다. 점수와 평가는 관리자가 확인합니다.
          </p>
          {failedSteps.length > 0 && (
            <p className="mt-3 rounded border border-warn-100 bg-warn-50 px-3 py-2 text-sm text-warn-600">
              일부 단계 채점에 실패했습니다. 관리자가 확인합니다.
            </p>
          )}
        </Panel>
      </div>
    );
  }

  // phase === "exam"
  const stepNumber = currentStep ? flow.indexOf(currentStep) + 1 : 0;
  const materialReady = stepMaterial?.feature_key === currentStep;
  const material = materialReady ? stepMaterial!.material : null;

  return (
    <div className="flex min-h-screen flex-col">
      {/* Slim exam bar: progress + overall timer */}
      <div className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-line bg-surface px-5 py-2.5">
        <div className="flex items-center gap-3">
          <SectionLabel>실전 모의고사</SectionLabel>
          <span className="font-mono text-xs text-ink-faint">
            {stepNumber} / {flow.length}
          </span>
          <ol className="hidden items-center gap-1.5 md:flex">
            {flow.map((step) => {
              const done = completedSteps.includes(step);
              const active = step === currentStep;
              return (
                <li
                  key={step}
                  className={
                    done
                      ? "rounded-sm px-2 py-0.5 text-[11px] font-medium text-good-600"
                      : active
                        ? "rounded-sm bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-600"
                        : "rounded-sm px-2 py-0.5 text-[11px] text-ink-faint"
                  }
                >
                  {STEP_LABELS[step]}
                  {done ? " ✓" : ""}
                </li>
              );
            })}
          </ol>
        </div>
        {remainingSeconds > 0 && (
          <CountdownTimer key={attemptId ?? "timer"} seconds={remainingSeconds} />
        )}
      </div>

      {error && (
        <p className="border-b border-bad-100 bg-bad-50 px-5 py-2 text-sm text-bad-600">{error}</p>
      )}

      {/* The step renders the SAME workspace as practice, in exam mode (score hidden). */}
      <div className="min-h-0 flex-1">
        {currentStep === "context_engineering" && (
          <ContextWorkspace
            key="context"
            projectId={CONTEXT_PROJECT_ID}
            examMode
            onExamSubmit={(claudeMd) =>
              handleSubmit("context_engineering", { claude_md: claudeMd })
            }
          />
        )}

        {currentStep === "spec_design" && (
          <SpecWorkbench
            key="spec"
            examMode
            examTaskId={SPEC_TASK_ID}
            onExamSubmit={(instruction) => handleSubmit("spec_design", { instruction })}
          />
        )}

        {currentStep === "rejection_eval" &&
          (materialReady ? (
            <div className="px-5 py-6">
              <RejectionWorkbench
                key="rejection"
                examMode
                examTopic={
                  {
                    index: (material!.topic_index as number) ?? 0,
                    title: material!.title as string,
                    description: material!.description as string,
                    requirements: (material!.requirements as string[]) ?? [],
                  } satisfies TopicMeta
                }
                onExamGenerate={generateRejection}
                onExamSubmit={(flaggedIds) =>
                  handleSubmit("rejection_eval", { flagged_ids: flaggedIds, reasons: {} })
                }
              />
            </div>
          ) : (
            <p className="px-5 py-8 text-ink-soft">불러오는 중…</p>
          ))}

        {currentStep === "test_design" &&
          (materialReady ? (
            <div className="px-5 py-6">
              <TestDesignWorkbench
                key="test"
                examMode
                examProblem={material as unknown as ProblemPublic}
                onExamSubmit={(flaws) => handleSubmit("test_design", { flaws })}
              />
            </div>
          ) : (
            <p className="px-5 py-8 text-ink-soft">불러오는 중…</p>
          ))}

        {currentStep === "dev_prompting" && (
          <DevWorkspace
            key="dev"
            problemId={DEV_PROBLEM_ID}
            examMode
            onExamSubmit={(prompts) => handleSubmit("dev_prompting", { prompts })}
          />
        )}
      </div>
    </div>
  );
}
