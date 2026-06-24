// Mirrors backend/feature_spec_design response models (see SPEC.md / api.py).

export type Grade = "excellent" | "good" | "fair" | "poor";
export type Quality = "good" | "ok" | "weak" | "bad" | "unspecified" | "unknown";

export interface TaskPublic {
  id: string;
  title: string;
  brief: string;
  requirement_count: number;
  dimension_count: number;
}

export interface RequirementResult {
  id: string;
  text: string;
  met_count: number;
  total: number;
  satisfaction: number; // 0..1
  satisfied: boolean;
}

export interface DimensionResult {
  key: string;
  label: string;
  distribution: Record<string, number>;
  top_value: string;
  agreement: number; // 0..1
  quality: Quality;
  quality_score: number; // 0..1
  score: number; // agreement × quality_score
  diverged: boolean;
}

export interface OverEngineeringItem {
  label: string;
  count: number;
  prevalence: number; // 0..1
}

export interface SpecScore {
  total: number; // 0..100
  base_score: number; // 3-axis blend before penalty
  requirement_score: number; // 0..100
  decision_score: number; // 0..100
  consistency: number; // 0..100
  overengineering_penalty: number; // points subtracted
  grade: Grade;
  failed_requirements: string[];
  weak_decisions: string[];
  diverged_decisions: string[];
  overengineered: string[];
  feedback: string;
}

export interface Sample {
  index: number;
  content: string;
}

export interface EvaluationResult {
  task_id: string;
  instruction: string;
  total_score: number;
  score: SpecScore;
  requirements: RequirementResult[];
  dimensions: DimensionResult[];
  overengineering: OverEngineeringItem[];
  samples: Sample[];
}
