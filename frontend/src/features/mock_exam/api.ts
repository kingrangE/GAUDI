// Thin client for the /api/mock-exam backend.
import type {
  AttemptStatus,
  FinishResponse,
  GenerateItemsResponse,
  StartResponse,
  SubmitStepResponse,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const mockExamApi = {
  start: (candidate_code: string) =>
    request<StartResponse>("/api/mock-exam/start", { candidate_code }),

  getAttempt: (attempt_id: string) =>
    request<AttemptStatus>(`/api/mock-exam/attempts/${attempt_id}`),

  getStepMaterial: (attempt_id: string, feature_key: string) =>
    request<Record<string, unknown>>(
      `/api/mock-exam/attempts/${attempt_id}/steps/${feature_key}`,
    ),

  generateRejection: (attempt_id: string, prompt: string) =>
    request<GenerateItemsResponse>(
      `/api/mock-exam/attempts/${attempt_id}/steps/rejection_eval/generate`,
      { prompt },
    ),

  submitStep: (attempt_id: string, feature_key: string, input: unknown) =>
    request<SubmitStepResponse>(
      `/api/mock-exam/attempts/${attempt_id}/steps/${feature_key}/submit`,
      input,
    ),

  finish: (attempt_id: string) =>
    request<FinishResponse>(`/api/mock-exam/attempts/${attempt_id}/finish`, {}),
};
