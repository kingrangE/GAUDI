// Typed fetch wrappers for the coding-test backend. No LLM calls here — the
// frontend only talks to the FastAPI backend.

import type {
  ProblemDetail,
  ProblemSummary,
  RunResponse,
  SubmissionCreated,
  SubmissionResult,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const PREFIX = "/api/coding-test";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`API ${res.status} ${res.statusText} (${path})`);
  }
  return (await res.json()) as T;
}

export function getProblems(): Promise<ProblemSummary[]> {
  return http<ProblemSummary[]>(`${PREFIX}/problems`);
}

export function getProblem(id: string): Promise<ProblemDetail> {
  return http<ProblemDetail>(`${PREFIX}/problems/${id}`);
}

export function runCode(id: string, code: string): Promise<RunResponse> {
  return http<RunResponse>(`${PREFIX}/problems/${id}/run`, {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export function createSubmission(payload: {
  problem_id: string;
  candidate_id: string;
  code: string;
}): Promise<SubmissionCreated> {
  return http<SubmissionCreated>(`${PREFIX}/submissions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getSubmission(id: string): Promise<SubmissionResult> {
  return http<SubmissionResult>(`${PREFIX}/submissions/${id}`);
}
