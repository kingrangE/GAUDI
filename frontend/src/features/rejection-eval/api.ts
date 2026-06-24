// Thin client for the rejection-eval backend API.
import type {
  CreateSessionResponse,
  GenerateResponse,
  ResultResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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

export function createSession(): Promise<CreateSessionResponse> {
  // Anonymous: the entry gate handles identity; no name is collected here.
  return request("/api/rejection-eval/sessions", {});
}

export function generateTopic(
  sessionId: string,
  topicIndex: number,
  prompt: string,
): Promise<GenerateResponse> {
  return request(
    `/api/rejection-eval/sessions/${sessionId}/topics/${topicIndex}/generate`,
    { prompt },
  );
}

export function submitTopic(
  sessionId: string,
  topicIndex: number,
  flaggedIds: string[],
  reasons: Record<string, string> = {},
): Promise<{ topic_index: number; submitted: boolean }> {
  return request(
    `/api/rejection-eval/sessions/${sessionId}/topics/${topicIndex}/submit`,
    { flagged_ids: flaggedIds, reasons },
  );
}

export function scoreSession(sessionId: string): Promise<ResultResponse> {
  return request(`/api/rejection-eval/sessions/${sessionId}/score`, {});
}

export function getResult(sessionId: string): Promise<ResultResponse> {
  return request(`/api/rejection-eval/sessions/${sessionId}/result`);
}
