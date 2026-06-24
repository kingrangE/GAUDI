"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
    <main>
      <p style={{ color: "#5f6368" }}>
        주제 {topicIndex + 1} / {TOTAL}
      </p>
      <h1>{topic ? topic.title : `주제 ${topicIndex + 1}`}</h1>
      {topic && <p>{topic.description}</p>}

      {phase === "prompt" ? (
        <section>
          <label style={{ display: "block", margin: "16px 0 8px" }}>
            AI에게 보낼 설계 지시(프롬프트)
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={6}
            style={{ width: "100%", padding: 8 }}
            placeholder="구체적으로 지시할수록 좋습니다."
          />
          <div style={{ marginTop: 12 }}>
            <button onClick={onGenerate} disabled={busy || !prompt.trim()}>
              {busy ? "생성 중…" : "AI 설계 생성"}
            </button>
          </div>
        </section>
      ) : (
        <section>
          <p>AI가 만든 설계 항목입니다. 잘못 적용된 기술이나 잘못된 방향성을 모두 거부(체크)하세요.</p>
          <ItemChecklist items={items} flagged={flagged} onToggle={toggle} />
          <div style={{ marginTop: 12 }}>
            <button onClick={onSubmit} disabled={busy}>
              {busy
                ? "처리 중…"
                : topicIndex < TOTAL - 1
                  ? "제출하고 다음 주제로"
                  : "제출하고 채점하기"}
            </button>
          </div>
        </section>
      )}
      {error && <p style={{ color: "#c5221f" }}>{error}</p>}
    </main>
  );
}
