// Mirrors backend/feature_context_engineering response models (see SPEC.md / router.py).

export interface FileNode {
  path: string;
  kind: "file" | "dir";
  content: string | null;
}

export interface Project {
  id: string;
  title: string;
  brief: string;
  files: FileNode[];
}

export interface Submission {
  project_id: string;
  claude_md: string;
}

export interface ComponentScore {
  name: string;
  score: number;
  detail: string;
}

export interface EvaluationResult {
  project_id: string;
  claude_md: string;
  scores: ComponentScore[];
  total: number;
}

export interface CriterionResult {
  id: string;
  text: string;
  category: string;
  covered: boolean;
  evidence: string;
}

export interface DimensionScore {
  key: string; // grounding | boundary | coverage | conciseness
  label: string;
  score: number; // 0–100
  weight: number;
  available: boolean; // false when an LLM was required but absent
  detail: string;
}

export interface EvaluationReport {
  project_id: string;
  scored: boolean;
  total: number; // weighted composite 0–100
  dimensions: DimensionScore[];
  results: CriterionResult[]; // per-criterion breakdown for the coverage axis
}
