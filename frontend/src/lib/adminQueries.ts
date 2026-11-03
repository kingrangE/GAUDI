import { requireAdminSession } from "./adminSessionServer";
import type { CandidateSummary, AttemptSummary, ExamResultDetail } from "./adminApi";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------- Fetch helpers ----------

async function adminFetch<T>(path: string): Promise<T> {
  const token = process.env.ADMIN_TOKEN;
  const res = await fetch(`${BASE}${path}`, {
    headers: token ? { "X-Admin-Token": token } : undefined,
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`admin API ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

/** Fetch helpers swallow connection errors so a backend-down demo still renders
 *  an empty state instead of a Next.js error page. */
export async function fetchCandidates(): Promise<CandidateSummary[]> {
  await requireAdminSession();
  try {
    return await adminFetch<CandidateSummary[]>("/api/admin/candidates");
  } catch {
    return [];
  }
}

export async function fetchExamResults(): Promise<AttemptSummary[]> {
  await requireAdminSession();
  try {
    return await adminFetch<AttemptSummary[]>("/api/admin/exam-results");
  } catch {
    return [];
  }
}

export async function fetchExamResult(id: string): Promise<ExamResultDetail | null> {
  await requireAdminSession();
  try {
    return await adminFetch<ExamResultDetail>(`/api/admin/exam-results/${id}`);
  } catch {
    return null;
  }
}
