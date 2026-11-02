"use client";

import { useCallback, useEffect, useState } from "react";

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
  const [savedSubmissions, setSavedSubmissions] = useState<Record<string, string>>({});
  const [resumeAvailable, setResumeAvailable] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const loadMaterial = useCallback(async (id: string, step: FeatureKey) => {
    const m = (await mockExamApi.getStepMaterial(id, step)) as unknown as StepMaterial;
    setStepMaterial(m);
  }, []);

  const restoreExam = useCallback(async () => {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (!stored) return;
    setResumeAvailable(true);
    setPhase("loading");
    setError(null);
    try {
      const status = await mockExamApi.getAttempt(stored);
      if (status.status === "finished" || status.status === "completed") {
        sessionStorage.removeItem(SESSION_KEY);
        setResumeAvailable(false);
        setPhase("done");
        return;
      }
      setAttemptId(stored);
      setFlow((status.flow as FeatureKey[]) ?? DEFAULT_FLOW);
      setCompletedSteps((status.completed_steps as FeatureKey[]) ?? []);
      setRemainingSeconds(status.remaining_seconds);
      setSavedSubmissions(status.submissions ?? {});
      const step = status.current_step as FeatureKey | null;
      setCurrentStep(step);
      if (step) {
        try { await loadMaterial(stored, step); }
        catch { setError("문제를 불러오지 못했습니다. 다시 시도해 주세요."); }
      }
      setPhase("exam");
    } catch {
      setError("저장된 시험에 연결하지 못했습니다. 연결을 확인하고 다시 시도해 주세요.");
      setPhase("intro");
    }
  }, [loadMaterial]);

  useEffect(() => { void restoreExam(); }, [restoreExam]);

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

  const finishExam = useCallback(async () => {
    if (!attemptId) return;
    setPhase("finishing");
    try {
      await mockExamApi.finish(attemptId);
      sessionStorage.removeItem(SESSION_KEY);
      setPhase("done");
    } catch {
      setError("종료하지 못했습니다. 저장된 답안의 채점을 확인한 뒤 다시 시도해 주세요.");
      setPhase("exam");
    }
  }, [attemptId]);

  const advance = useCallback(async (feature: FeatureKey, next: string | null) => {
    if (!attemptId) return;
    setCompletedSteps((prev) => [...new Set([...prev, feature])]);
    setSavedSubmissions((prev) => ({ ...prev, [feature]: "graded" }));
    if (next) {
      setCurrentStep(next as FeatureKey);
      await loadMaterial(attemptId, next as FeatureKey);
    } else {
      await finishExam();
    }
  }, [attemptId, loadMaterial, finishExam]);

  const handleSubmit = useCallback(async (feature: FeatureKey, input: unknown) => {
    if (!attemptId) return;
    setError(null);
    try {
      const result = await mockExamApi.submitStep(attemptId, feature, input);
      await advance(feature, result.next_step);
    } catch (error) {
      setError("제출을 확인하지 못했습니다. 답안을 유지한 채 다시 시도해 주세요.");
      try {
        const status = await mockExamApi.getAttempt(attemptId);
        setSavedSubmissions(status.submissions ?? {});
      } catch { /* The current editor retains the input while offline. */ }
      throw error;
    }
  }, [attemptId, advance]);

  const retrySaved = useCallback(async (feature: FeatureKey) => {
    if (!attemptId) return;
    setRetrying(true);
    setError(null);
    try {
      const result = await mockExamApi.retryStep(attemptId, feature);
      await advance(feature, result.next_step);
    } catch {
      setError("재채점하지 못했습니다. 진행 중인 채점은 잠시 후 다시 확인해 주세요.");
    } finally {
      setRetrying(false);
    }
  }, [attemptId, advance]);

  const loadDevRun = useCallback(() => mockExamApi.getDevRun(attemptId!), [attemptId]);
  const runDevTurn = useCallback((prompt: string, turn: number) =>
    mockExamApi.runDevTurn(attemptId!, prompt, turn), [attemptId]);

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
            <Button onClick={() => void (resumeAvailable ? restoreExam() : startExam())}>
              {resumeAvailable ? "저장된 시험 다시 연결" : "시험 시작"}
            </Button>
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
          <CountdownTimer key={attemptId ?? "timer"} seconds={remainingSeconds}
            onExpire={() => setRemainingSeconds(0)} />
        )}
      </div>

      {error && (
        <p className="border-b border-bad-100 bg-bad-50 px-5 py-2 text-sm text-bad-600">{error}</p>
      )}

      {Object.entries(savedSubmissions).filter(([, state]) => state !== "graded").map(([feature, state]) => (
        <div key={feature} className="border-b border-line bg-paper px-5 py-3">
          <p>{STEP_LABELS[feature as FeatureKey]}: 저장된 답안 ({state === "failed" ? "채점 실패" : "채점 대기/진행 중"})</p>
          <Button disabled={retrying} onClick={() => void retrySaved(feature as FeatureKey)}>
            저장된 답안 재채점
          </Button>
        </div>
      ))}
      {(remainingSeconds <= 0 || currentStep === null) && (
        <div className="px-5 py-6">
          <p>{remainingSeconds <= 0 ? "제한 시간이 종료되었습니다." : "모든 답안을 제출했습니다."}</p>
          <Button onClick={() => void finishExam()}>시험 종료</Button>
        </div>
      )}

      {error && currentStep && stepMaterial?.feature_key !== currentStep && attemptId && (
        <Button onClick={() => void loadMaterial(attemptId, currentStep).then(() => setError(null))
          .catch(() => setError("문제를 불러오지 못했습니다. 다시 시도해 주세요."))}>
          문제 다시 불러오기
        </Button>
      )}

      {/* The step renders the SAME workspace as practice, in exam mode (score hidden). */}
      <div className="min-h-0 flex-1" hidden={remainingSeconds <= 0 && currentStep !== "dev_prompting"}>
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
            examExpired={remainingSeconds <= 0}
            onExamRun={runDevTurn}
            loadExamRun={loadDevRun}
            onExamSubmit={(prompts) => handleSubmit("dev_prompting", { prompts })}
          />
        )}
      </div>
    </div>
  );
}
