import { queuedFetch } from "./jobs";

export function isDemoEnabled(): boolean {
  return process.env.NEXT_PUBLIC_DEMO_ENABLED === "true";
}

interface DemoSession {
  session_id: string;
  expires_at: string;
}

let sessionRequest: Promise<DemoSession> | null = null;

/** Reuse the HttpOnly cookie on reload; concurrent feature requests share issuance. */
export function ensureDemoSession(): Promise<DemoSession> {
  if (!sessionRequest) {
    const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
    sessionRequest = fetch(`${base}/api/demo/session`, {
      method: "POST",
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw new Error("체험 세션을 시작하지 못했습니다. 다시 시도해 주세요.");
      return response.json() as Promise<DemoSession>;
    }).catch((error: unknown) => {
      sessionRequest = null;
      throw error;
    });
  }
  return sessionRequest;
}

export async function demoFetch(url: string, init?: RequestInit): Promise<Response> {
  if (!isDemoEnabled()) return init === undefined ? fetch(url) : fetch(url, init);
  const visitor = await ensureDemoSession();
  const options: RequestInit = { ...init, credentials: "include" };
  const response = init?.method?.toUpperCase() === "POST"
    ? await queuedFetch(url, options, visitor.session_id)
    : await fetch(url, options);
  if (response.status === 401) {
    sessionRequest = null;
    throw new Error("체험 세션이 만료되었습니다. 입장 화면에서 다시 시작해 주세요.");
  }
  if ([409, 429, 503].includes(response.status)) {
    const body = await response.clone().json().catch(() => null) as { detail?: string } | null;
    const detail = body?.detail ?? "";
    if (detail.startsWith("demo ") || detail.startsWith("this feature ") ||
        detail.startsWith("accepted demo ")) {
      const message = detail.includes("queue") ? "현재 체험 요청이 많습니다. 잠시 후 다시 시도해 주세요." :
        detail.includes("budget") ? "오늘 체험 가능한 예산이 모두 예약되었거나 소진되었습니다. 나중에 다시 방문해 주세요." :
        response.status === 503 ? "체험 준비 중입니다. 잠시 후 다시 시도해 주세요." :
        "이 기능의 체험이 이미 시작되었거나 허용된 실행 횟수를 사용했습니다. 시작한 체험을 이어서 진행해 주세요.";
      throw new Error(message);
    }
  }
  return response;
}
