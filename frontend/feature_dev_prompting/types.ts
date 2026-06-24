// Mirrors backend/feature_dev_prompting response models (see SPEC.md / api.py).

export interface CaseResult {
  index: number;
  hidden: boolean;
  passed: boolean;
  status: string; // pass | wrong_answer | runtime_error | timeout
  expected: string | null;
  got: string | null;
}

export interface TurnResult {
  turn: number;
  prompt: string;
  code: string;
  passed_count: number;
  total: number;
  solved: boolean;
  feedback: string;
  case_results: CaseResult[];
}

export interface ScoreBreakdown {
  total: number;
  pass_score: number;
  understanding_score: number;
  best_pass_rate: number;
  solved: boolean;
  solved_turn: number | null;
}

export interface EvaluationResult {
  problem_id: string;
  solved: boolean;
  score: ScoreBreakdown;
  turns: TurnResult[];
}

export interface Example {
  args: unknown[];
  expected: unknown;
}

export interface ProblemPublic {
  id: string;
  title: string;
  statement: string;
  constraints: string;
  entry_point: string;
  starter_code: string;
  time_limit_sec: number;
  examples: Example[];
  public_example_count: number;
}
