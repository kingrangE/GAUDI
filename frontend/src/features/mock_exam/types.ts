// Types mirroring the /api/mock-exam contract.

export type FeatureKey =
  | "context_engineering"
  | "spec_design"
  | "rejection_eval"
  | "test_design"
  | "dev_prompting";

export interface StartResponse {
  attempt_id: string;
  flow: string[];
  current_step: string;
  remaining_seconds: number;
}

export interface AttemptStatus {
  flow: string[];
  completed_steps: string[];
  current_step: string | null;
  remaining_seconds: number;
  status: "in_progress" | "finished" | "completed";
}

export interface RejectionItem {
  id: string;
  text: string;
}

export interface GenerateItemsResponse {
  items: RejectionItem[];
}

export interface SubmitStepResponse {
  recorded: boolean;
  next_step: string | null;
}

export interface FinishResponse {
  completed: boolean;
}
