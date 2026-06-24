"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/Badge";
import { useProblems } from "../queries";

function difficultyTone(difficulty: string): "good" | "warn" | "bad" | "neutral" {
  const d = difficulty.toLowerCase();
  if (d === "easy") return "good";
  if (d === "medium") return "warn";
  if (d === "hard") return "bad";
  return "neutral";
}

export function ProblemList() {
  const { data, isPending, isError } = useProblems();

  if (isPending) return <p className="text-ink-soft">불러오는 중…</p>;
  if (isError || !data) return <p className="text-bad-600">문제를 불러오지 못했습니다.</p>;

  return (
    <ul className="grid grid-cols-3 gap-3">
      {data.map((problem) => (
        <li key={problem.id}>
          <Link
            href={`/coding-test/${problem.id}`}
            className="flex items-center justify-between rounded-xl border border-line bg-surface p-4 shadow-panel transition-colors hover:border-brand-300"
          >
            <span className="font-medium text-ink-900">{problem.title}</span>
            <Badge tone={difficultyTone(problem.difficulty)}>{problem.difficulty}</Badge>
          </Link>
        </li>
      ))}
    </ul>
  );
}
