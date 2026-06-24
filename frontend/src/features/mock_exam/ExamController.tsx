"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { CodePanel } from "@/components/ui/CodePanel";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { CountdownTimer } from "@/features/cs_eval/components/CountdownTimer";
import { getUserCode } from "@/lib/accessCodes";

import { mockExamApi } from "./api";
import type { FeatureKey, RejectionItem } from "./types";

const STEP_LABELS: Record<FeatureKey, string> = {
  context_engineering: "컨텍스트 엔지니어링",
  spec_design: "사양 설계",
  rejection_eval: "반려 평가",
  test_design: "테스트 설계",
  dev_prompting: "개발 프롬프팅",
};

const DEFAULT_FLOW: FeatureKey[] = [
  "context_engineering",
  "spec_design",
  "rejection_eval",
  "test_design",
  "dev_prompting",
];

const SESSION_KEY = "mockExam:attemptId";

type Phase = "intro" | "loading" | "exam" | "done";

export function ExamController() {
  const [phase, setPhase] = useState<Phase>("intro");
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [flow, setFlow] = useState<FeatureKey[]>(DEFAULT_FLOW);
  const [completedSteps, setCompletedSteps] = useState<FeatureKey[]>([]);
  const [currentStep, setCurrentStep] = useState<FeatureKey | null>(null);
  const [stepMaterial, setStepMaterial] = useState<Record<string, unknown>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step-specific input state
  const [claudeMd, setClaudeMd] = useState("");
  const [instruction, setInstruction] = useState("");
  const [rejectionPrompt, setRejectionPrompt] = useState("");
  const [rejectionItems, setRejectionItems] = useState<RejectionItem[]>([]);
  const [flaggedIds, setFlaggedIds] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [flaws, setFlaws] = useState<string[]>(["", "", ""]);
  const [prompts, setPrompts] = useState<string[]>(["", "", ""]);

  const resetStepInputs = useCallback(() => {
    setClaudeMd("");
    setInstruction("");
    setRejectionPrompt("");
    setRejectionItems([]);
    setFlaggedIds([]);
    setGenerating(false);
    setFlaws(["", "", ""]);
    setPrompts(["", "", ""]);
  }, []);

  // On mount: restore in-progress attempt from sessionStorage.
  useEffect(() => {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (!stored) return;

    mockExamApi
      .getAttempt(stored)
      .then((status) => {
        if (status.status === "finished") {
          sessionStorage.removeItem(SESSION_KEY);
          return;
        }
        setAttemptId(stored);
        setFlow((status.flow as FeatureKey[]) ?? DEFAULT_FLOW);
        setCompletedSteps((status.completed_steps as FeatureKey[]) ?? []);
        setRemainingSeconds(status.remaining_seconds);

        if (status.remaining_seconds <= 0) {
          void mockExamApi.finish(stored).then(() => {
            sessionStorage.removeItem(SESSION_KEY);
            setPhase("done");
          });
          return;
        }

        const step = status.current_step as FeatureKey | null;
        setCurrentStep(step);

        if (step) {
          void mockExamApi.getStepMaterial(stored, step).then(setStepMaterial);
        }
        setPhase("exam");
      })
      .catch(() => {
        sessionStorage.removeItem(SESSION_KEY);
      });
  }, []);

  const startExam = useCallback(async () => {
    setPhase("loading");
    setError(null);
    try {
      const code = getUserCode() ?? "ANON";
      const res = await mockExamApi.start(code);
      sessionStorage.setItem(SESSION_KEY, res.attempt_id);
      setAttemptId(res.attempt_id);
      setFlow((res.flow as FeatureKey[]) ?? DEFAULT_FLOW);
      setCurrentStep(res.current_step as FeatureKey);
      setRemainingSeconds(res.remaining_seconds);
      const material = await mockExamApi.getStepMaterial(res.attempt_id, res.current_step);
      setStepMaterial(material);
      setPhase("exam");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("intro");
    }
  }, []);

  const submitStep = useCallback(async () => {
    if (!attemptId || !currentStep || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      let input: unknown;
      switch (currentStep) {
        case "context_engineering":
          input = { claude_md: claudeMd };
          break;
        case "spec_design":
          input = { instruction };
          break;
        case "rejection_eval":
          input = { flagged_ids: flaggedIds, reasons: {} };
          break;
        case "test_design":
          input = { flaws: flaws.filter(Boolean) };
          break;
        case "dev_prompting":
          input = { prompts: prompts.filter(Boolean) };
          break;
        default:
          input = {};
      }

      const res = await mockExamApi.submitStep(attemptId, currentStep, input);
      setCompletedSteps((prev) => [...prev, currentStep]);

      if (!res.next_step) {
        await mockExamApi.finish(attemptId);
        sessionStorage.removeItem(SESSION_KEY);
        setPhase("done");
      } else {
        const nextStep = res.next_step as FeatureKey;
        setCurrentStep(nextStep);
        resetStepInputs();
        const material = await mockExamApi.getStepMaterial(attemptId, nextStep);
        setStepMaterial(material);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }, [
    attemptId,
    currentStep,
    submitting,
    claudeMd,
    instruction,
    flaggedIds,
    flaws,
    prompts,
    resetStepInputs,
  ]);

  const generateItems = useCallback(async () => {
    if (!attemptId || generating || !rejectionPrompt.trim()) return;
    setGenerating(true);
    try {
      const res = await mockExamApi.generateRejection(attemptId, rejectionPrompt);
      setRejectionItems(res.items);
      setFlaggedIds([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(false);
    }
  }, [attemptId, rejectionPrompt, generating]);

  // ---- Render ----

  if (phase === "intro") {
    return (
      <div className="flex min-h-[400px] items-center justify-center py-10">
        <Panel className="w-full max-w-xl text-center">
          <SectionLabel>실전 모의고사</SectionLabel>
          <h1 className="mt-3 text-2xl font-bold tracking-tight text-ink-900">시험을 시작합니다</h1>
          <p className="mt-3 text-sm text-ink-soft">
            5단계(컨텍스트 · 사양 · 반려 · 테스트 · 프롬프팅)를 순서대로 진행합니다.
            <br />
            점수는 시험 종료 후 관리자가 확인합니다.
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
      <div className="flex min-h-[400px] items-center justify-center">
        <span className="text-ink-soft">시험을 시작하는 중…</span>
      </div>
    );
  }

  if (phase === "done") {
    return (
      <div className="flex min-h-[400px] items-center justify-center py-10">
        <Panel className="w-full max-w-xl text-center">
          <SectionLabel>완료</SectionLabel>
          <h1 className="mt-3 text-2xl font-bold tracking-tight text-ink-900">수고하셨습니다</h1>
          <p className="mt-3 text-sm text-ink-soft">점수는 관리자 확인</p>
        </Panel>
      </div>
    );
  }

  // phase === "exam"
  const stepIndex = currentStep ? flow.indexOf(currentStep) : -1;
  const stepNumber = stepIndex + 1;
  const totalSteps = flow.length;

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-line bg-surface px-6 py-3 shadow-panel">
        <SectionLabel>실전 모의고사</SectionLabel>
        {remainingSeconds > 0 && (
          <CountdownTimer key={attemptId ?? "timer"} seconds={remainingSeconds} />
        )}
      </div>

      <div className="flex flex-1 gap-6 p-6">
        {/* Left: step progress */}
        <aside className="w-52 shrink-0">
          <Panel>
            <SectionLabel>진행 현황</SectionLabel>
            <ol className="mt-4 space-y-3">
              {flow.map((step, i) => {
                const done = completedSteps.includes(step);
                const active = step === currentStep;
                return (
                  <li key={step} className="flex items-center gap-2 text-sm">
                    <span
                      className={
                        done
                          ? "shrink-0 font-mono text-good-600"
                          : active
                            ? "shrink-0 font-mono font-semibold text-brand-600"
                            : "shrink-0 font-mono text-ink-faint"
                      }
                    >
                      {i + 1}
                    </span>
                    <span
                      className={
                        done
                          ? "flex-1 text-ink-soft line-through"
                          : active
                            ? "flex-1 font-medium text-ink-900"
                            : "flex-1 text-ink-faint"
                      }
                    >
                      {STEP_LABELS[step]}
                    </span>
                    {done && (
                      <Badge tone="good" className="shrink-0 text-[10px]">
                        완료
                      </Badge>
                    )}
                  </li>
                );
              })}
            </ol>
          </Panel>
        </aside>

        {/* Main content */}
        <div className="flex min-w-0 flex-1 flex-col gap-4">
          {error && (
            <p className="rounded border border-bad-100 bg-bad-50 px-3 py-2 text-sm text-bad-600">
              {error}
            </p>
          )}

          <Panel>
            <div className="mb-5 flex items-center gap-3">
              <Badge tone="brand">
                {stepNumber} / {totalSteps}
              </Badge>
              <h2 className="text-lg font-semibold text-ink-900">
                {currentStep ? STEP_LABELS[currentStep] : ""}
              </h2>
            </div>

            {currentStep === "context_engineering" && (
              <ContextStep material={stepMaterial} value={claudeMd} onChange={setClaudeMd} />
            )}
            {currentStep === "spec_design" && (
              <SpecStep material={stepMaterial} value={instruction} onChange={setInstruction} />
            )}
            {currentStep === "rejection_eval" && (
              <RejectionStep
                material={stepMaterial}
                prompt={rejectionPrompt}
                onPromptChange={setRejectionPrompt}
                items={rejectionItems}
                flaggedIds={flaggedIds}
                onToggle={(id) =>
                  setFlaggedIds((prev) =>
                    prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
                  )
                }
                onGenerate={() => void generateItems()}
                generating={generating}
              />
            )}
            {currentStep === "test_design" && (
              <TestDesignStep flaws={flaws} onChange={setFlaws} />
            )}
            {currentStep === "dev_prompting" && (
              <DevPromptingStep prompts={prompts} onChange={setPrompts} />
            )}
          </Panel>

          <div className="flex justify-end">
            <Button onClick={() => void submitStep()} disabled={submitting}>
              {submitting ? "제출 중…" : "제출하고 다음 →"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---- Step input panels ----

function ContextStep({
  material,
  value,
  onChange,
}: {
  material: Record<string, unknown>;
  value: string;
  onChange: (v: string) => void;
}) {
  const theme = material.theme as string | undefined;
  return (
    <div className="space-y-4">
      {theme && (
        <CodePanel label="주제">
          <pre className="m-0 whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-ink-text">
            {theme}
          </pre>
        </CodePanel>
      )}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-ink-900">CLAUDE.md 작성</label>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={12}
          placeholder="프로젝트 컨텍스트를 CLAUDE.md 형식으로 작성하세요…"
          className="w-full resize-y rounded-md border border-line bg-surface p-3 font-mono text-sm text-ink-900 placeholder:text-ink-faint focus:border-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-600"
        />
      </div>
    </div>
  );
}

function SpecStep({
  material,
  value,
  onChange,
}: {
  material: Record<string, unknown>;
  value: string;
  onChange: (v: string) => void;
}) {
  const theme = material.theme as string | undefined;
  return (
    <div className="space-y-4">
      {theme && (
        <CodePanel label="주제">
          <pre className="m-0 whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-ink-text">
            {theme}
          </pre>
        </CodePanel>
      )}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-ink-900">사양 명세 작성</label>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={10}
          placeholder="기능 요구사항과 설계 지침을 작성하세요…"
          className="w-full resize-y rounded-md border border-line bg-surface p-3 text-sm text-ink-900 placeholder:text-ink-faint focus:border-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-600"
        />
      </div>
    </div>
  );
}

function RejectionStep({
  material,
  prompt,
  onPromptChange,
  items,
  flaggedIds,
  onToggle,
  onGenerate,
  generating,
}: {
  material: Record<string, unknown>;
  prompt: string;
  onPromptChange: (v: string) => void;
  items: RejectionItem[];
  flaggedIds: string[];
  onToggle: (id: string) => void;
  onGenerate: () => void;
  generating: boolean;
}) {
  const theme = material.theme as string | undefined;
  const flaggedSet = new Set(flaggedIds);
  return (
    <div className="space-y-4">
      {theme && (
        <CodePanel label="주제">
          <pre className="m-0 whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-ink-text">
            {theme}
          </pre>
        </CodePanel>
      )}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-ink-900">
          AI에게 설계 검토 요청하기
        </label>
        <div className="flex gap-2">
          <textarea
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            rows={3}
            placeholder="설계 검토를 요청하는 프롬프트를 입력하세요…"
            className="flex-1 resize-y rounded-md border border-line bg-surface p-3 text-sm text-ink-900 placeholder:text-ink-faint focus:border-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-600"
          />
          <Button
            variant="secondary"
            onClick={onGenerate}
            disabled={generating || !prompt.trim()}
            className="self-start"
          >
            {generating ? "생성 중…" : "생성"}
          </Button>
        </div>
      </div>
      {items.length > 0 && (
        <div>
          <SectionLabel className="mb-2 block">검토 항목 — 문제가 있는 항목을 거부하세요</SectionLabel>
          <ul className="space-y-2">
            {items.map((item) => {
              const flagged = flaggedSet.has(item.id);
              return (
                <li key={item.id}>
                  <label
                    className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                      flagged
                        ? "border-bad-100 bg-bad-50"
                        : "border-line hover:border-brand-300"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={flagged}
                      onChange={() => onToggle(item.id)}
                      aria-label={`거부: ${item.text}`}
                      className="mt-0.5 h-4 w-4 accent-bad-600"
                    />
                    <span className="text-sm leading-relaxed text-ink-900">{item.text}</span>
                    {flagged && (
                      <Badge tone="bad" className="ml-auto shrink-0">
                        거부
                      </Badge>
                    )}
                  </label>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

function TestDesignStep({
  flaws,
  onChange,
}: {
  flaws: string[];
  onChange: (flaws: string[]) => void;
}) {
  const updateFlaw = (i: number, v: string) => {
    const next = [...flaws];
    next[i] = v;
    onChange(next);
  };
  const addFlaw = () => onChange([...flaws, ""]);
  const removeFlaw = (i: number) => onChange(flaws.filter((_, idx) => idx !== i));

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-ink-900">발견한 결함 목록</p>
      {flaws.map((flaw, i) => (
        <div key={i} className="flex gap-2">
          <input
            type="text"
            value={flaw}
            onChange={(e) => updateFlaw(i, e.target.value)}
            placeholder={`결함 ${i + 1}…`}
            aria-label={`결함 ${i + 1}`}
            className="flex-1 rounded-md border border-line bg-surface px-3 py-2 text-sm text-ink-900 placeholder:text-ink-faint focus:border-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-600"
          />
          {flaws.length > 1 && (
            <button
              type="button"
              onClick={() => removeFlaw(i)}
              aria-label={`결함 ${i + 1} 제거`}
              className="px-2 text-sm text-ink-faint hover:text-bad-600"
            >
              ✕
            </button>
          )}
        </div>
      ))}
      <Button variant="secondary" onClick={addFlaw}>
        + 결함 추가
      </Button>
    </div>
  );
}

function DevPromptingStep({
  prompts,
  onChange,
}: {
  prompts: string[];
  onChange: (prompts: string[]) => void;
}) {
  const updatePrompt = (i: number, v: string) => {
    const next = [...prompts];
    next[i] = v;
    onChange(next);
  };
  const addPrompt = () => onChange([...prompts, ""]);
  const removePrompt = (i: number) => onChange(prompts.filter((_, idx) => idx !== i));

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-ink-900">AI 에이전트 지시 프롬프트</p>
      {prompts.map((p, i) => (
        <div key={i} className="flex gap-2">
          <textarea
            value={p}
            onChange={(e) => updatePrompt(i, e.target.value)}
            rows={4}
            placeholder={`프롬프트 ${i + 1}…`}
            aria-label={`프롬프트 ${i + 1}`}
            className="flex-1 resize-y rounded-md border border-line bg-surface px-3 py-2 text-sm text-ink-900 placeholder:text-ink-faint focus:border-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-600"
          />
          {prompts.length > 1 && (
            <button
              type="button"
              onClick={() => removePrompt(i)}
              aria-label={`프롬프트 ${i + 1} 제거`}
              className="px-2 text-sm text-ink-faint hover:text-bad-600"
            >
              ✕
            </button>
          )}
        </div>
      ))}
      <Button variant="secondary" onClick={addPrompt}>
        + 프롬프트 추가
      </Button>
    </div>
  );
}
