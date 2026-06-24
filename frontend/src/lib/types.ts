// Shared API types — mirror backend app/features/test_design/schemas.py.

export interface ProblemPublic {
  index: number;
  id: string;
  title: string;
  difficulty: string;
  // Prose scenario (service + feature + tech + how it's built). No code to review.
  spec: string;
  // Basic tests assumed already implemented — shown as a starting point.
  provided_tests: string[];
}

export interface CreateSessionResponse {
  session_id: string;
  candidate_name: string;
  problems: ProblemPublic[];
}

export interface SubmitResponse {
  problem_index: number;
  submitted: boolean;
}

export interface ResultFlaw {
  id: string;
  text: string;
  severity: string;
  category: string;
  found: boolean;
  quality: number;
  matched_candidate_text: string | null;
}

export interface ResultProblem {
  problem_index: number;
  problem_id: string;
  title: string;
  difficulty: string;
  provided_tests: string[];
  candidate_flaws: string[];
  flaws: ResultFlaw[];
  false_positives: string[];
  recall: number;
  precision: number;
  mean_quality: number;
  weighted_score: number;
  report: string;
}

export interface ResultResponse {
  session_id: string;
  candidate_name: string;
  status: string;
  recall: number;
  precision: number;
  weighted_score: number;
  problems: ResultProblem[];
}
