// Types mirroring the backend `/api/office-prompting` contract.

export interface ProblemMeta {
  index: number;
  title: string;
  description: string;
  target_entity: string;
  max_runs: number;
}

export interface DatasetTable {
  name: string;
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface CreateSessionResponse {
  session_id: string;
  candidate_name: string;
  problems: ProblemMeta[];
  datasets: DatasetTable[];
}

/** A run response deliberately carries NO correctness — only the rows the AI
 *  returned, so the candidate can verify output without seeing the score. */
export interface RunResponse {
  problem_index: number;
  run_number: number;
  runs_used: number;
  runs_remaining: number;
  predicted_ids: string[];
  predicted_rows: Record<string, unknown>[];
}

export interface ResultProblem {
  problem_index: number;
  title: string;
  target_entity: string;
  final_prompt: string;
  predicted_ids: string[];
  truth_ids: string[];
  tp: number;
  fp: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
  correct_count: number;
  truth_count: number;
}

export interface ResultResponse {
  session_id: string;
  candidate_name: string;
  status: string;
  precision: number;
  recall: number;
  f1: number;
  total_correct: number;
  problems: ResultProblem[];
}
