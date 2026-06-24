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

// ---------- Per-feature raw_result shapes (all fields optional — render defensively) ----------

export interface ContextEngineeringRaw {
  total?: number;
  scored?: number;
  dimensions?: Array<{
    key: string;
    label: string;
    score: number;
    weight: number;
    available: number;
    detail?: string;
  }>;
  results?: Array<{
    id: string;
    text: string;
    category: string;
    covered: boolean;
    evidence?: string;
    agreement?: boolean;
  }>;
}

export interface SpecDesignRaw {
  total?: number;
  total_score?: number;
  score?: {
    total?: number;
    requirement_score?: number;
    decision_score?: number;
    consistency?: number;
    grade?: string;
    overengineering_penalty?: number;
    failed_requirements?: string[];
    weak_decisions?: string[];
    feedback?: string;
  };
  requirements?: Array<{
    id: string;
    text: string;
    satisfaction: number;
    satisfied: boolean;
  }>;
  dimensions?: Array<{
    key: string;
    label: string;
    top_value?: number;
    agreement?: number;
    quality?: number;
    score?: number;
  }>;
  overengineering?: unknown[];
  samples?: Array<{ index: number; content: string }>;
}

export interface RejectionEvalRaw {
  f1?: number;
  precision?: number;
  recall?: number;
  items?: Array<{
    id: string;
    text: string;
    is_flawed: boolean;
    flaw_type?: string;
    outcome?: "caught" | "missed" | "false_alarm" | "correct_accept";
    flagged: boolean;
  }>;
  report?: string;
}

export interface TestDesignRaw {
  weighted_score?: number;
  recall?: number;
  precision?: number;
  mean_quality?: number;
  flaws?: Array<{
    id: string;
    text: string;
    severity?: string;
    category?: string;
    found: boolean;
    quality?: number;
    matched_candidate_text?: string;
  }>;
  false_positives?: unknown[];
  report?: string;
}

export interface DevPromptingRaw {
  total?: number;
  solved?: boolean;
  score?: {
    total?: number;
    pass_score?: number;
    understanding_score?: number;
    best_pass_rate?: number;
    solved_turn?: number | null;
  };
  turns?: Array<{
    turn: number;
    prompt: string;
    code: string;
    passed_count: number;
    total: number;
    solved: boolean;
    feedback?: string;
  }>;
}

// ---------- Discriminated union by feature_key ----------

/** Exam steps in evaluation order. */
export const EXAM_FLOW = [
  "context_engineering",
  "spec_design",
  "rejection_eval",
  "test_design",
  "dev_prompting",
] as const;

export type KnownFeatureKey = (typeof EXAM_FLOW)[number];

/** Full Korean step labels (detail view headings). */
export const STEP_LABELS: Record<KnownFeatureKey, string> = {
  context_engineering: "컨텍스트 엔지니어링",
  spec_design: "명세 설계",
  rejection_eval: "거부 평가",
  test_design: "테스트 설계",
  dev_prompting: "개발 프롬프팅",
};

/** Short monospace labels for mini bars in the candidate card. */
export const MINI_STEP_LABELS: Record<KnownFeatureKey, string> = {
  context_engineering: "CTX",
  spec_design: "SPEC",
  rejection_eval: "REJ",
  test_design: "TEST",
  dev_prompting: "DEV",
};

type RawMap = {
  context_engineering: ContextEngineeringRaw;
  spec_design: SpecDesignRaw;
  rejection_eval: RejectionEvalRaw;
  test_design: TestDesignRaw;
  dev_prompting: DevPromptingRaw;
};

type FeatureBase = { label: string; normalized_score: number; summary: string | null };

/** Discriminated union — narrow via `feature.feature_key`. */
export type FeatureResult = {
  [K in KnownFeatureKey]: FeatureBase & { feature_key: K; raw_result: RawMap[K] | null };
}[KnownFeatureKey];

export type ExamResultDetail = AttemptSummary & {
  features: FeatureResult[];
};

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

// ---------- Sort ----------

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

// ---------- Formatters ----------

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

/** Elapsed time in whole minutes between two ISO timestamps (null if incomplete). */
export function elapsedMinutes(startedAt: string, completedAt: string | null): number | null {
  if (!completedAt) return null;
  const start = new Date(startedAt).getTime();
  const end = new Date(completedAt).getTime();
  if (Number.isNaN(start) || Number.isNaN(end)) return null;
  return Math.round((end - start) / 60000);
}

/** Human-readable elapsed time ("45분", "1시간 30분"). */
export function formatElapsed(startedAt: string, completedAt: string | null): string {
  const mins = elapsedMinutes(startedAt, completedAt);
  if (mins === null) return "—";
  if (mins < 60) return `${mins}분`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m === 0 ? `${h}시간` : `${h}시간 ${m}분`;
}
