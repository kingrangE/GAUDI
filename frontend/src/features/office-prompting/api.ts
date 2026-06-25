// Thin client for the office-prompting backend API.
import type { CreateSessionResponse, ResultResponse, RunResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

// Anonymous by default: the entry gate handles identity, so the page starts a
// session without prompting for a name. Backend requires a non-empty name.
export function createSession(candidateName = "익명"): Promise<CreateSessionResponse> {
  return request("/api/office-prompting/sessions", { candidate_name: candidateName });
}

export function runProblem(
  sessionId: string,
  problemIndex: number,
  prompt: string,
): Promise<RunResponse> {
  return request(
    `/api/office-prompting/sessions/${sessionId}/problems/${problemIndex}/run`,
    { prompt },
  );
}

export function scoreSession(sessionId: string): Promise<ResultResponse> {
  return request(`/api/office-prompting/sessions/${sessionId}/score`, {});
}

export function getResult(sessionId: string): Promise<ResultResponse> {
  return request(`/api/office-prompting/sessions/${sessionId}/result`);
}
