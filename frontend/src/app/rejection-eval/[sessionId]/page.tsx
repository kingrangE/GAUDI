"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { CodeMeta, CodePanel } from "@/components/ui/CodePanel";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { generateTopic, scoreSession, submitTopic } from "@/features/rejection-eval/api";
import { ItemChecklist } from "@/features/rejection-eval/components/ItemChecklist";
import type { PublicItem, TopicMeta } from "@/features/rejection-eval/types";

const TOTAL = 3;

export default function EvalPage() {
  const router = useRouter();
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;

  const [topics, setTopics] = useState<TopicMeta[]>([]);
  const [topicIndex, setTopicIndex] = useState(0);
  const [phase, setPhase] = useState<"prompt" | "review">("prompt");
  const [prompt, setPrompt] = useState("");
  const [items, setItems] = useState<PublicItem[]>([]);
  const [flagged, setFlagged] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem(`reval:topics:${sessionId}`);
    if (raw) setTopics(JSON.parse(raw) as TopicMeta[]);
  }, [sessionId]);

  const topic = topics[topicIndex];

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
      const res = await generateTopic(sessionId, topicIndex, prompt.trim());
      setItems(res.items);
      setFlagged([]);
      setPhase("review");
    } catch (e) {
      setError(e instanceof Error ? e.message : "생성 실패");
    } finally {
      setBusy(false);
    }
  }

  async function onSubmit() {
    setBusy(true);
    setError(null);
    try {
      await submitTopic(sessionId, topicIndex, flagged);
      if (topicIndex < TOTAL - 1) {
        setTopicIndex((i) => i + 1);
        setPrompt("");
        setItems([]);
        setFlagged([]);
        setPhase("prompt");
      } else {
        await scoreSession(sessionId);
        router.push(`/rejection-eval/${sessionId}/result`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "제출 실패");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* progress */}
      <div className="flex items-center gap-3">
        <Badge tone="brand">
          주제 {topicIndex + 1} / {TOTAL}
        </Badge>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-line">
          <div
            className="h-full rounded-full bg-brand-600 transition-all"
            style={{ width: `${((topicIndex + (phase === "review" ? 0.5 : 0)) / TOTAL) * 100}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] gap-4">
        {/* Left — topic context */}
        <Panel className="h-fit">
          <SectionLabel>주제</SectionLabel>
          <h1 className="mt-2 text-lg font-bold text-ink-900">
            {topic ? topic.title : `주제 ${topicIndex + 1}`}
          </h1>
          {topic ? <p className="mt-2 text-sm leading-relaxed text-ink-soft">{topic.description}</p> : null}
          <p className="mt-4 rounded-lg bg-paper p-3 text-xs leading-relaxed text-ink-soft">
            {phase === "prompt"
              ? "AI에게 설계를 지시하는 프롬프트를 작성하세요. 구체적일수록 좋습니다."
              : "AI가 만든 설계 항목 중 잘못 적용된 기술이나 잘못된 방향성을 모두 거부(체크)하세요."}
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
              placeholder="예) 결제 시스템을 설계해줘. 동시성, 데이터 정합성, 장애 복구를 고려해…"
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
            <CodePanel
              label="AGENT OUTPUT"
              meta={<CodeMeta>설계 항목 {items.length}</CodeMeta>}
            >
              <ItemChecklist items={items} flagged={flagged} onToggle={toggle} />
            </CodePanel>
            <div className="flex items-center justify-between">
              <span className="text-sm text-ink-soft">{flagged.length}개 거부함</span>
              <Button onClick={onSubmit} disabled={busy}>
                {busy
                  ? "처리 중…"
                  : topicIndex < TOTAL - 1
                    ? "제출하고 다음 주제로"
                    : "제출하고 채점하기"}
              </Button>
            </div>
          </div>
        )}
      </div>
      {error ? <p className="text-sm text-bad-600">{error}</p> : null}
    </div>
  );
}
