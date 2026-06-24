import type { CreateSessionResponse, ResultResponse, SubmitResponse } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export function createSession(candidateName: string): Promise<CreateSessionResponse> {
  return jsonFetch<CreateSessionResponse>("/test-design/sessions", {
    method: "POST",
    body: JSON.stringify({ candidate_name: candidateName }),
  });
}

export function submitProblem(
  sessionId: string,
  problemIndex: number,
  flaws: string[],
): Promise<SubmitResponse> {
  return jsonFetch<SubmitResponse>(
    `/test-design/sessions/${sessionId}/problems/${problemIndex}/submit`,
    { method: "POST", body: JSON.stringify({ flaws }) },
  );
}

export function getResult(sessionId: string): Promise<ResultResponse> {
  return jsonFetch<ResultResponse>(`/test-design/sessions/${sessionId}/result`);
}
