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
  return response;
}
