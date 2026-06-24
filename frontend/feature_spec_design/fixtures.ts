// Test fixtures (only imported by *.test files; not exported from the barrel).

import type {
  DimensionResult,
  EvaluationResult,
  RequirementResult,
  Sample,
  SpecScore,
  TaskPublic,
} from "./types";

export function makeRequirement(over: Partial<RequirementResult> = {}): RequirementResult {
  const satisfaction = over.satisfaction ?? 1;
  return {
    id: "signup",
    text: "이메일과 비밀번호로 회원가입할 수 있다",
    met_count: Math.round(satisfaction * 10),
    total: 10,
    satisfaction,
    satisfied: satisfaction >= 0.7,
    ...over,
  };
}

export function makeDimension(over: Partial<DimensionResult> = {}): DimensionResult {
  const agreement = over.agreement ?? 1;
  const quality_score = over.quality_score ?? 1;
  return {
    key: "password_storage",
    label: "비밀번호 저장 방식",
    distribution: { bcrypt: 10 },
    top_value: "bcrypt",
    agreement,
    quality: "good",
    quality_score,
    score: Math.round(agreement * quality_score * 10000) / 10000,
    diverged: false,
    ...over,
  };
}

export function makeResult(over: Partial<EvaluationResult> = {}): EvaluationResult {
  const requirements = over.requirements ?? [makeRequirement()];
  const dimensions = over.dimensions ?? [makeDimension()];
  const samples: Sample[] = over.samples ?? [{ index: 0, content: "결정: FastAPI / PostgreSQL" }];
  const score: SpecScore = {
    total: 100,
    requirement_score: 100,
    decision_score: 100,
    consistency: 100,
    grade: "excellent",
    failed_requirements: [],
    weak_decisions: [],
    diverged_decisions: [],
    feedback: "요구사항을 모두 충족하고 설계 결정도 일관되고 견고합니다.",
    ...over.score,
  };
  return {
    task_id: over.task_id ?? "login-signup",
    instruction: over.instruction ?? "FastAPI, PostgreSQL, bcrypt, JWT",
    total_score: over.total_score ?? score.total,
    score,
    requirements,
    dimensions,
    samples,
  };
}

export const SAMPLE_TASKS: TaskPublic[] = [
  {
    id: "login-signup",
    title: "로그인 / 회원가입 기능 구현",
    brief: "로그인 회원가입 brief",
    requirement_count: 7,
    dimension_count: 5,
  },
  {
    id: "file-upload-api",
    title: "파일 업로드 API 구현",
    brief: "파일 업로드 brief",
    requirement_count: 4,
    dimension_count: 4,
  },
];
