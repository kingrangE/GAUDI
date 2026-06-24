// TypeScript mirror of the backend coding-test API contract (PR-A).

export type SubmissionStatus = "grading" | "graded" | "failed";

export interface ProblemSummary {
  id: string;
  title: string;
  difficulty: string;
}

export interface SampleCase {
  args: unknown[];
  expected: unknown;
}

export interface ProblemDetail {
  id: string;
  title: string;
  description_md: string;
  function_name: string;
  starter_code: string;
  difficulty: string;
  sample_cases: SampleCase[];
}

export interface CaseRunResult {
  index: number;
  passed: boolean;
  error: string | null;
}

export interface RunResponse {
  results: CaseRunResult[];
}

export interface SubmissionCreated {
  submission_id: string;
  status: SubmissionStatus;
}

export interface SubmissionResult {
  id: string;
  problem_id: string;
  candidate_id: string;
  status: SubmissionStatus;
  test_passed: number | null;
  test_total: number | null;
  strengths: string[] | null;
  weaknesses: string[] | null;
  analysis_report: string | null;
  code_quality_score: number | null;
  error: string | null;
}
