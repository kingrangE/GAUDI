// TypeScript mirror of the backend cs-eval API contract (PR-A).

export type SessionStatus = "grading" | "graded" | "failed";
export type ResponseType =
  | "correct"
  | "partial"
  | "honest_unknown"
  | "bluff_wrong";

export interface Question {
  id: string;
  domain: string;
  prompt_md: string;
  ordinal: number;
}

export interface AnswerInput {
  question_id: string;
  answer_text: string;
}

export interface SessionCreated {
  session_id: string;
  status: SessionStatus;
}

export interface AnswerResult {
  question_id: string;
  domain: string;
  response_type: ResponseType | null;
  score: number | null;
  matched_keywords: string[] | null;
  missing_keywords: string[] | null;
  rationale: string | null;
}

export interface SessionResult {
  id: string;
  candidate_id: string;
  status: SessionStatus;
  total_score: number | null;
  normalized_score: number | null;
  summary_report: string | null;
  analysis_report: string | null;
  per_question: AnswerResult[];
  error: string | null;
}
