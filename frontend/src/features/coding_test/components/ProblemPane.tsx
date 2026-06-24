"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";

import { Badge } from "@/components/ui/Badge";
import { Tabs } from "@/components/ui/Tabs";
import type { ProblemDetail } from "../types";
import { CountdownTimer } from "./CountdownTimer";

function difficultyTone(difficulty: string): "good" | "warn" | "bad" | "neutral" {
  const d = difficulty.toLowerCase();
  if (d === "easy") return "good";
  if (d === "medium") return "warn";
  if (d === "hard") return "bad";
  return "neutral";
}

export function ProblemPane({
  problem,
  timerSeconds,
}: {
  problem: ProblemDetail;
  timerSeconds: number;
}) {
  const [tab, setTab] = useState("problem");

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between gap-2">
        <Tabs
          tabs={[
            { id: "problem", label: "문제" },
            { id: "examples", label: "예시" },
          ]}
          active={tab}
          onChange={setTab}
        />
        <div className="flex items-center gap-2">
          <Badge tone={difficultyTone(problem.difficulty)}>{problem.difficulty}</Badge>
          <CountdownTimer seconds={timerSeconds} />
        </div>
      </div>

      <h1 className="mt-3 text-lg font-bold text-ink-900">{problem.title}</h1>

      <div className="mt-3 min-h-0 flex-1 overflow-y-auto">
        {tab === "problem" ? (
          <article className="space-y-2 text-sm leading-relaxed text-ink-soft [&_code]:rounded [&_code]:bg-paper [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-[0.85em] [&_h2]:mt-4 [&_h2]:font-semibold [&_h3]:mt-3 [&_h3]:font-semibold [&_li]:ml-4 [&_li]:list-disc [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-ink-900 [&_pre]:p-3 [&_pre]:text-ink-text">
            <ReactMarkdown>{problem.description_md}</ReactMarkdown>
          </article>
        ) : (
          <div className="space-y-3">
            {problem.sample_cases.length === 0 ? (
              <p className="text-sm text-ink-faint">예시가 없습니다.</p>
            ) : (
              problem.sample_cases.map((c, i) => (
                <div
                  key={i}
                  className="code-surface rounded-lg border border-ink-600 p-3 font-mono text-xs text-ink-text"
                >
                  <div className="text-ink-muted">예시 {i + 1}</div>
                  <div className="mt-1 break-words">
                    입력: {problem.function_name}(
                    {c.args.map((a) => JSON.stringify(a)).join(", ")})
                  </div>
                  <div className="break-words">출력: {JSON.stringify(c.expected)}</div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
