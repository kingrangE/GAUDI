// Types mirroring the backend `/api/rejection-eval` contract.

export interface TopicMeta {
  index: number;
  title: string;
  description: string;
  /** The fixed functional requirements (the "문제") shown to the candidate. */
  requirements: string[];
}

export interface CreateSessionResponse {
  session_id: string;
  candidate_name: string;
  topics: TopicMeta[];
}

export interface PublicItem {
  id: string;
  text: string;
}

export interface GenerateResponse {
  topic_index: number;
  items: PublicItem[];
}

export type Outcome =
  | "caught"
  | "missed"
  | "false_alarm"
  | "correct_accept"
  | "bonus_found";

export type FlawType = "wrong_tech" | "wrong_direction" | "none";

/** Why an item had to be rejected: an injected wrong design, or a decision
 * not in the requirements (out of scope), or not a flaw at all. */
export type FlawSource = "injected" | "out_of_scope" | "none";

export interface ResultItem {
  id: string;
  text: string;
  is_flawed: boolean;
  flaw_type: FlawType;
  in_requirements: boolean;
  flaw_source: FlawSource;
  explanation: string;
  flagged: boolean;
  outcome: Outcome;
}

export interface ResultTopic {
  topic_index: number;
  topic_title: string;
  prompt: string;
  items: ResultItem[];
  precision: number;
  recall: number;
  f1: number;
  report: string;
}

export interface ResultResponse {
  session_id: string;
  candidate_name: string;
  status: string;
  precision: number;
  recall: number;
  f1: number;
  topics: ResultTopic[];
}
