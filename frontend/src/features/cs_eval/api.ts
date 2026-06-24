// Typed fetch wrappers for the cs-eval backend. No LLM calls here — the
// frontend only talks to the FastAPI backend.

import type { AnswerInput, Question, SessionCreated, SessionResult } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const PREFIX = "/api/cs-eval";

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

export function getQuestions(): Promise<Question[]> {
  return http<Question[]>(`${PREFIX}/questions`);
}

export function createSession(payload: {
  candidate_id: string;
  answers: AnswerInput[];
}): Promise<SessionCreated> {
  return http<SessionCreated>(`${PREFIX}/sessions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getSession(id: string): Promise<SessionResult> {
  return http<SessionResult>(`${PREFIX}/sessions/${id}`);
}
