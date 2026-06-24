// HTTP client for the dev-prompting backend. The client never calls an LLM directly.

import type { EvaluationResult, ProblemPublic } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function readJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(`요청 실패 (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function fetchProblems(): Promise<ProblemPublic[]> {
  const res = await fetch(`${API_BASE}/dev-prompting/problems`);
  return readJson<ProblemPublic[]>(res);
}

export async function fetchProblem(problemId: string): Promise<ProblemPublic> {
  const res = await fetch(`${API_BASE}/dev-prompting/problems/${problemId}`);
  return readJson<ProblemPublic>(res);
}

export async function runEvaluation(
  problemId: string,
  prompts: string[],
): Promise<EvaluationResult> {
  const res = await fetch(`${API_BASE}/dev-prompting/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ problem_id: problemId, prompts }),
  });
  return readJson<EvaluationResult>(res);
}
