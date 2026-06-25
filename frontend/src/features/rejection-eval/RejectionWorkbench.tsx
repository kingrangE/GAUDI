"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { CodeMeta, CodePanel } from "@/components/ui/CodePanel";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { createSession, generateTopic, submitTopic } from "./api";
import { ItemChecklist } from "./components/ItemChecklist";
import type { PublicItem, TopicMeta } from "./types";

export interface RejectionWorkbenchProps {
  /**
   * When true, runs in exam mode:
   *  - topic picker hidden; examTopic (or a placeholder) is shown instead
   *  - generation delegates to onExamGenerate
   *  - submission delegates to onExamSubmit; no score button, no navigation
   */
  examMode?: boolean;
  /** The topic to display in exam mode (caller-provided). */
  examTopic?: TopicMeta;
  /** Exam mode: generate items for the given prompt, return { id, text }[]. */
  onExamGenerate?: (prompt: string) => Promise<PublicItem[]>;
  /** Exam mode: submit the flagged item IDs; called instead of navigating to result. */
  onExamSubmit?: (flaggedIds: string[]) => Promise<void>;
}

export function RejectionWorkbench({
  examMode,
  examTopic,
  onExamGenerate,
  onExamSubmit,
}: RejectionWorkbenchProps) {
  const router = useRouter();

  // ── Practice-mode state ──────────────────────────────────────────────────
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [topics, setTopics] = useState<TopicMeta[]>([]);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(!examMode); // exam mode skips session creation

  // ── Shared state ─────────────────────────────────────────────────────────
  const [phase, setPhase] = useState<"prompt" | "review">("prompt");
  const [prompt, setPrompt] = useState("");
  const [items, setItems] = useState<PublicItem[]>([]);
  const [flagged, setFlagged] = useState<string[]>([]);
  const [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Exam-mode: auto-generate items from topic requirements on mount ────────
  useEffect(() => {
    if (!examMode || !examTopic || !onExamGenerate) return;
    let active = true;
    setBusy(true);
    const autoPrompt = examTopic.requirements.join("\n");
    onExamGenerate(autoPrompt)
      .then((generatedItems) => {
        if (!active) return;
        setItems(generatedItems);
        setFlagged([]);
        setPhase("review");
      })
      .catch(() => {
        if (!active) return;
        setError("AI 설계 생성에 실패했습니다. 잠시 후 다시 시도하세요.");
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [examMode, examTopic, onExamGenerate]);

  // ── Practice-mode session bootstrap ──────────────────────────────────────
  useEffect(() => {
    if (examMode) return; // exam mode doesn't create its own session

    let active = true;
    createSession()
      .then((session) => {
        if (!active) return;
        setSessionId(session.session_id);
        setTopics(session.topics);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError("세션을 시작하지 못했습니다. 백엔드가 실행 중인지 확인하세요.");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [examMode]);

  // ── Derived ───────────────────────────────────────────────────────────────
  const topic: TopicMeta | undefined = examMode ? examTopic : topics[selected];
  const locked = phase === "review";

  // ── Handlers ─────────────────────────────────────────────────────────────
  function toggle(id: string) {
    setFlagged((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function onGenerate() {
    if (!prompt.trim()) return;
    setBusy(true);
    setError(null);
    try {
      let generatedItems: PublicItem[];
      if (examMode && onExamGenerate) {
        generatedItems = await onExamGenerate(prompt.trim());
      } else {
        if (!sessionId) return;
        const res = await generateTopic(sessionId, selected, prompt.trim());
        generatedItems = res.items;
      }
      setItems(generatedItems);
      setFlagged([]);
      setPhase("review");
    } catch {
      setError("AI 설계 생성에 실패했습니다. 잠시 후 다시 시도하세요.");
    } finally {
      setBusy(false);
    }
  }

  async function onSubmit() {
    setBusy(true);
    setError(null);
    try {
      if (examMode && onExamSubmit) {
        await onExamSubmit(flagged);
      } else {
        if (!sessionId) return;
        await submitTopic(sessionId, selected, flagged);
      }
      setSubmitted(true);
    } catch {
      setError("제출에 실패했습니다. 잠시 후 다시 시도하세요.");
    } finally {
      setBusy(false);
    }
  }

  function onScore() {
    if (!sessionId) return;
    router.push(`/rejection-eval/result/${sessionId}`);
  }

  // ── Loading / error guards ────────────────────────────────────────────────
  if (examMode && busy && phase === "prompt") {
    return <p className="py-8 text-ink-soft">AI 설계 항목을 불러오는 중…</p>;
  }
  if (!examMode && loading) {
    return <p className="py-8 text-ink-soft">평가를 준비하는 중…</p>;
  }
  if (!examMode && topics.length === 0) {
    return (
      <p className="py-8 text-bad-600">{error ?? "주제를 불러오지 못했습니다."}</p>
    );
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4 py-6">
      <div>
        <p className="text-sm font-semibold text-brand-600">거부 능력</p>
        <h1 className="text-xl font-bold text-ink-900">거부 능력 평가</h1>
      </div>

      {/* Topic picker — hidden in exam mode */}
      {!examMode && (
        <Panel className="flex flex-wrap items-center justify-between gap-3">
          <label htmlFor="topic-picker" className="flex items-center gap-2 text-sm">
            <span className="font-medium text-ink-900">주제 선택</span>
            <select
              id="topic-picker"
              aria-label="주제 선택"
              value={selected}
              disabled={locked}
              onChange={(e) => setSelected(Number(e.target.value))}
              className="rounded-md border border-line bg-paper px-3 py-1.5 font-mono text-sm text-ink-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100 disabled:opacity-60"
            >
              {topics.map((t) => (
                <option key={t.index} value={t.index}>
                  {t.title}
                </option>
              ))}
            </select>
          </label>
          {locked ? (
            <Badge tone="brand">진행 중 — 주제 고정됨</Badge>
          ) : (
            <span className="text-sm text-ink-soft">한 개의 주제를 골라 진행합니다.</span>
          )}
        </Panel>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        {/* Left — topic + requirements (the 문제) */}
        <Panel className="h-fit">
          <SectionLabel>주제</SectionLabel>
          {topic ? (
            <>
              <h2 className="mt-2 text-lg font-bold text-ink-900">{topic.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">{topic.description}</p>
              {topic.requirements.length > 0 && (
                <div className="mt-4">
                  <SectionLabel>기능 요구사항</SectionLabel>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-relaxed text-ink-900">
                    {topic.requirements.map((req, i) => (
                      <li key={i}>{req}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <p className="mt-2 text-sm text-ink-soft">주제를 불러오는 중…</p>
          )}
          <p className="mt-4 rounded-lg bg-paper p-3 text-xs leading-relaxed text-ink-soft">
            {phase === "prompt"
              ? "위 기능 요구사항을 만족하도록 AI에게 설계를 지시하는 프롬프트를 작성하세요."
              : "AI 설계 항목 중 잘못 적용된 기술·방향성, 그리고 요구사항에 없는 항목을 모두 거부(체크)하세요."}
          </p>
        </Panel>

        {/* Right — action */}
        {phase === "prompt" ? (
          <Panel className="flex flex-col">
            <SectionLabel>INSTRUCT THE AGENT</SectionLabel>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={10}
              placeholder="예) 요구사항을 만족하도록 설계해줘. 인증·저장·검증 방식까지 구체적으로…"
              className="mt-3 w-full flex-1 resize-none rounded-lg border border-line p-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
            />
            <div className="mt-3">
              <Button onClick={onGenerate} disabled={busy || !prompt.trim()}>
                {busy ? "생성 중…" : "AI 설계 생성"}
              </Button>
            </div>
          </Panel>
        ) : (
          <div className="flex flex-col gap-3">
            <CodePanel label="AGENT OUTPUT" meta={<CodeMeta>설계 항목 {items.length}</CodeMeta>}>
              <ItemChecklist items={items} flagged={flagged} onToggle={toggle} />
            </CodePanel>
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm text-ink-soft">{flagged.length}개 거부함</span>
              {submitted ? (
                /* In exam mode, never show the score button or navigate */
                examMode ? (
                  <span className="text-sm text-good-600">제출 완료</span>
                ) : (
                  <Button onClick={onScore}>채점</Button>
                )
              ) : (
                <Button onClick={onSubmit} disabled={busy}>
                  {busy ? "제출 중…" : "제출"}
                </Button>
              )}
            </div>
            {submitted && !examMode ? (
              <p className="text-sm text-good-600">제출됨 — 채점을 누르면 결과를 확인합니다.</p>
            ) : null}
          </div>
        )}
      </div>

      {error ? <p className="text-sm text-bad-600">{error}</p> : null}
    </div>
  );
}
