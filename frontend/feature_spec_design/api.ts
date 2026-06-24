// HTTP client for the spec-design backend. The client never calls an LLM directly.

import type { EvaluationResult, TaskPublic } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function readJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(`요청 실패 (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function fetchTasks(): Promise<TaskPublic[]> {
  const res = await fetch(`${API_BASE}/spec-design/tasks`);
  return readJson<TaskPublic[]>(res);
}

export async function runEvaluation(
  taskId: string,
  instruction: string,
): Promise<EvaluationResult> {
  const res = await fetch(`${API_BASE}/spec-design/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_id: taskId, instruction }),
  });
  return readJson<EvaluationResult>(res);
}
