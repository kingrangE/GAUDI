export type AdminTone = "teal" | "blue" | "amber" | "red" | "green";

export type AdminMetric = {
  id: string;
  label: string;
  value: string;
  detail: string;
  tone: AdminTone;
};

export type EvaluationStatus = "pending" | "reviewing" | "flagged" | "done";
export type RiskLevel = "low" | "medium" | "high";
export type TrackId = "agent" | "office" | "codingCs";

export type EvaluationQueueItem = {
  id: string;
  candidate: string;
  track: string;
  status: EvaluationStatus;
  score: number | null;
  submittedAt: string;
  risk: RiskLevel;
};

export type ProblemSet = {
  id: string;
  name: string;
  category: string;
  owner: string;
  itemCount: number;
  status: "draft" | "ready" | "running";
  primaryMetric: string;
};

export type EvaluationSession = {
  id: string;
  name: string;
  mode: "demo" | "pilot" | "official";
  participants: number;
  completed: number;
  remainingMinutes: number;
  status: "ready" | "running" | "closed";
};

export type CandidateResult = {
  id: string;
  name: string;
  role: string;
  totalScore: number;
  completedAt: string;
  strengths: string[];
  weaknesses: string[];
  tracks: {
    agentRejection: number;
    specDesign: number;
    contextEngineering: number;
    codingCs: number;
    officePrompting: number;
  };
};

export type AdminActivity = {
  id: string;
  actor: string;
  action: string;
  target: string;
  happenedAt: string;
};

export type TrackDashboard = {
  id: TrackId;
  name: string;
  shortName: string;
  description: string;
  pendingReviews: number;
  averageScore: number;
  flaggedCount: number;
  resultRoute: string;
  tests: Array<{
    id: string;
    name: string;
    metric: string;
    status: EvaluationStatus;
  }>;
};

export const adminMetrics: AdminMetric[] = [
  {
    id: "participants",
    label: "평가 축",
    value: "3",
    detail: "Agent, Office, Coding/CS",
    tone: "teal",
  },
  {
    id: "completed",
    label: "제출 완료",
    value: "19",
    detail: "완료율 79%",
    tone: "green",
  },
  {
    id: "flagged",
    label: "검토 필요",
    value: "7",
    detail: "맹신/허위 답변 감지",
    tone: "amber",
  },
  {
    id: "reports",
    label: "리포트 생성",
    value: "16",
    detail: "요약/분석 리포트 포함",
    tone: "blue",
  },
];

export const trackDashboards: TrackDashboard[] = [
  {
    id: "agent",
    name: "Agent 활용 개발 역량 평가",
    shortName: "Agent 개발",
    description: "AI 답변 검증, 거부 판단, 명세 구체화, Context Engineering을 본다.",
    pendingReviews: 9,
    averageScore: 74,
    flaggedCount: 4,
    resultRoute: "/admin/tracks/agent",
    tests: [
      {
        id: "AG-REJ",
        name: "AI 거부 능력",
        metric: "Precision / Recall",
        status: "reviewing",
      },
      {
        id: "AG-SPEC",
        name: "구체적인 설계 지시",
        metric: "응답 분산 / 명세 밀도",
        status: "pending",
      },
      {
        id: "AG-CTX",
        name: "CLAUDE.md 설계",
        metric: "Context completeness",
        status: "done",
      },
    ],
  },
  {
    id: "office",
    name: "사무직 Prompting",
    shortName: "Office Prompting",
    description: "데이터 분석, 인사이트 도출, 업무 산출물 품질을 본다.",
    pendingReviews: 3,
    averageScore: 82,
    flaggedCount: 1,
    resultRoute: "/admin/tracks/office",
    tests: [
      {
        id: "OF-INSIGHT",
        name: "업무 인사이트 도출",
        metric: "정확도 / 실행 가능성",
        status: "reviewing",
      },
      {
        id: "OF-DATA",
        name: "데이터 분석 Prompt",
        metric: "분석 관점 다양성",
        status: "done",
      },
    ],
  },
  {
    id: "codingCs",
    name: "전통 코테/CS 세부 평가",
    shortName: "Coding/CS",
    description: "정답 여부보다 알고리즘 선택 근거와 CS 서술의 정확도를 본다.",
    pendingReviews: 6,
    averageScore: 69,
    flaggedCount: 2,
    resultRoute: "/admin/tracks/coding-cs",
    tests: [
      {
        id: "CS-ALG",
        name: "알고리즘 이해 진단",
        metric: "선택 근거 / 결함 위치",
        status: "reviewing",
      },
      {
        id: "CS-WRITTEN",
        name: "CS 서술형",
        metric: "정확 / 모름 / 아는 척",
        status: "pending",
      },
    ],
  },
];

export const evaluationQueue: EvaluationQueueItem[] = [
  {
    id: "EV-1048",
    candidate: "김도윤",
    track: "AI 거부 능력",
    status: "flagged",
    score: 61,
    submittedAt: "15:20",
    risk: "high",
  },
  {
    id: "EV-1047",
    candidate: "박서연",
    track: "Context Engineering",
    status: "reviewing",
    score: 78,
    submittedAt: "15:04",
    risk: "medium",
  },
  {
    id: "EV-1046",
    candidate: "이준호",
    track: "기술 명세 설계",
    status: "pending",
    score: null,
    submittedAt: "14:49",
    risk: "low",
  },
  {
    id: "EV-1045",
    candidate: "최민지",
    track: "전통 코테/CS",
    status: "done",
    score: 91,
    submittedAt: "14:31",
    risk: "low",
  },
];

export const problemSets: ProblemSet[] = [
  {
    id: "PS-AGENT-01",
    name: "Agent 개발 역량 종합",
    category: "Agent Evaluation",
    owner: "혁신",
    itemCount: 5,
    status: "running",
    primaryMetric: "검증/거부/명세",
  },
  {
    id: "PS-OFFICE-01",
    name: "사무직 Prompting TOP",
    category: "Office Prompting",
    owner: "민수",
    itemCount: 8,
    status: "ready",
    primaryMetric: "업무 인사이트",
  },
  {
    id: "PS-CS-01",
    name: "코테/CS 세부 진단",
    category: "Coding CS",
    owner: "길원",
    itemCount: 6,
    status: "draft",
    primaryMetric: "부분 지식 분석",
  },
  {
    id: "PS-ZIP-01",
    name: "과제 zip 채점",
    category: "Assignment",
    owner: "혁신",
    itemCount: 2,
    status: "draft",
    primaryMetric: "완성도/테스트",
  },
];

export const sessions: EvaluationSession[] = [
  {
    id: "SE-001",
    name: "해커톤 데모 평가",
    mode: "demo",
    participants: 9,
    completed: 6,
    remainingMinutes: 28,
    status: "running",
  },
  {
    id: "SE-002",
    name: "사무직 Prompting 파일럿",
    mode: "pilot",
    participants: 7,
    completed: 7,
    remainingMinutes: 0,
    status: "closed",
  },
  {
    id: "SE-003",
    name: "개발자 CS 서술형",
    mode: "official",
    participants: 8,
    completed: 6,
    remainingMinutes: 42,
    status: "running",
  },
];

export const candidateResults: CandidateResult[] = [
  {
    id: "candidate-1",
    name: "김도윤",
    role: "Backend Developer",
    totalScore: 76,
    completedAt: "15:20",
    strengths: ["테스트 설계", "CS 부분 지식"],
    weaknesses: ["AI 답변 검증", "명세 구체성"],
    tracks: {
      agentRejection: 58,
      specDesign: 70,
      contextEngineering: 73,
      codingCs: 84,
      officePrompting: 77,
    },
  },
  {
    id: "candidate-2",
    name: "박서연",
    role: "Product Manager",
    totalScore: 88,
    completedAt: "15:04",
    strengths: ["Context Engineering", "업무형 Prompting"],
    weaknesses: ["알고리즘 근거 설명"],
    tracks: {
      agentRejection: 86,
      specDesign: 90,
      contextEngineering: 94,
      codingCs: 71,
      officePrompting: 96,
    },
  },
  {
    id: "candidate-3",
    name: "이준호",
    role: "Frontend Developer",
    totalScore: 64,
    completedAt: "14:49",
    strengths: ["구현 프롬프팅"],
    weaknesses: ["허위 설계 탐지", "CS 서술 정확도", "테스트 명세"],
    tracks: {
      agentRejection: 51,
      specDesign: 63,
      contextEngineering: 68,
      codingCs: 61,
      officePrompting: 77,
    },
  },
];

export const adminActivities: AdminActivity[] = [
  {
    id: "A-501",
    actor: "hyeoksin",
    action: "주의 항목 메모 갱신",
    target: "EV-1048",
    happenedAt: "2분 전",
  },
  {
    id: "A-500",
    actor: "gilwon",
    action: "테스트 작성 Skill 초안 등록",
    target: "PS-CS-01",
    happenedAt: "18분 전",
  },
  {
    id: "A-499",
    actor: "minsu",
    action: "디자인 목업 검토 요청",
    target: "관리자 결과 화면",
    happenedAt: "42분 전",
  },
];

export function getQueueCounts(items: EvaluationQueueItem[]) {
  return items.reduce(
    (counts, item) => {
      counts[item.status] += 1;
      return counts;
    },
    {
      pending: 0,
      reviewing: 0,
      flagged: 0,
      done: 0,
    } satisfies Record<EvaluationStatus, number>,
  );
}

export function getHighRiskItems(items: EvaluationQueueItem[]) {
  return items.filter((item) => item.risk === "high");
}

export function getSessionProgress(session: EvaluationSession) {
  if (session.participants === 0) {
    return 0;
  }

  return Math.round((session.completed / session.participants) * 100);
}

export function getCandidateResult(id: string) {
  return candidateResults.find((result) => result.id === id);
}

export function getTrackDashboard(id: TrackId) {
  return trackDashboards.find((track) => track.id === id);
}

export function sortCandidateResults(
  results: CandidateResult[],
  sort: "score-desc" | "score-asc" | "time-desc" | "time-asc",
) {
  const sorted = [...results];

  if (sort === "score-asc") {
    return sorted.sort((a, b) => a.totalScore - b.totalScore);
  }

  if (sort === "time-asc") {
    return sorted.sort((a, b) => a.completedAt.localeCompare(b.completedAt));
  }

  if (sort === "time-desc") {
    return sorted.sort((a, b) => b.completedAt.localeCompare(a.completedAt));
  }

  return sorted.sort((a, b) => b.totalScore - a.totalScore);
}
