// Map a backend case status to a judge verdict (the page's structural vocabulary).

export type VerdictTone = "ac" | "wa" | "tle" | "re" | "pending";

export interface Verdict {
  short: string; // AC / WA / TLE / RE
  label: string; // 맞았습니다 / 틀렸습니다 / 시간 초과 / 런타임 에러
  tone: VerdictTone;
}

export function verdictFor(status: string): Verdict {
  switch (status) {
    case "pass":
      return { short: "AC", label: "맞았습니다", tone: "ac" };
    case "wrong_answer":
      return { short: "WA", label: "틀렸습니다", tone: "wa" };
    case "timeout":
      return { short: "TLE", label: "시간 초과", tone: "tle" };
    case "runtime_error":
      return { short: "RE", label: "런타임 에러", tone: "re" };
    default:
      return { short: "··", label: "채점 대기", tone: "pending" };
  }
}
