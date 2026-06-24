/**
 * Admin read client for the mock-exam (모의고사) results API.
 *
 * The backend exposes `/api/admin/*` which is rooted at `exam_attempts`, so only
 * mock-exam results are reachable here — practice runs are never returned.
 * Used from server components; fetches are uncached so the console always shows
 * the latest submissions.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type AttemptStatus = "in_progress" | "completed" | "failed";

export type AttemptSummary = {
  id: string;
  candidate_code: string;
  candidate_label: string;
  status: AttemptStatus;
  overall_normalized: number | null;
  started_at: string;
  completed_at: string | null;
  feature_count: number;
};

export type CandidateSummary = {
  code: string;
  label: string;
  latest_attempt: AttemptSummary | null;
};

export type FeatureResult = {
  feature_key: string;
  label: string;
  normalized_score: number;
  summary: string | null;
  raw_result: Record<string, unknown> | null;
};

export type ExamResultDetail = AttemptSummary & {
  features: FeatureResult[];
};

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
  try {
    return await adminFetch<CandidateSummary[]>("/api/admin/candidates");
  } catch {
    return [];
  }
}

export async function fetchExamResults(): Promise<AttemptSummary[]> {
  try {
    return await adminFetch<AttemptSummary[]>("/api/admin/exam-results");
  } catch {
    return [];
  }
}

export async function fetchExamResult(id: string): Promise<ExamResultDetail | null> {
  try {
    return await adminFetch<ExamResultDetail>(`/api/admin/exam-results/${id}`);
  } catch {
    return null;
  }
}

export type AttemptSort = "score-desc" | "score-asc" | "time-desc" | "time-asc";

/** Sort attempts for the results table. Nulls (un-scored / in-progress) sink to
 *  the bottom on score sorts. */
export function sortAttempts(
  attempts: AttemptSummary[],
  sort: AttemptSort,
): AttemptSummary[] {
  const sorted = [...attempts];
  const score = (a: AttemptSummary) =>
    a.overall_normalized ?? Number.NEGATIVE_INFINITY;
  const time = (a: AttemptSummary) => a.completed_at ?? a.started_at;

  switch (sort) {
    case "score-asc":
      return sorted.sort((a, b) => score(a) - score(b));
    case "score-desc":
      return sorted.sort((a, b) => score(b) - score(a));
    case "time-asc":
      return sorted.sort((a, b) => time(a).localeCompare(time(b)));
    default:
      return sorted.sort((a, b) => time(b).localeCompare(time(a)));
  }
}

const STATUS_LABELS: Record<AttemptStatus, string> = {
  in_progress: "진행 중",
  completed: "완료",
  failed: "실패",
};

export function statusLabel(status: AttemptStatus): string {
  return STATUS_LABELS[status] ?? status;
}

/** Short, locale-independent HH:MM from an ISO timestamp (or "—"). */
export function formatTime(iso: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

export function formatScore(score: number | null): string {
  return score === null ? "—" : String(Math.round(score));
}
