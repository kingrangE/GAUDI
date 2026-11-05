/** One observer per owned job; only identifiers and request paths survive a reload. */
export interface JobState {
  status: "queued" | "running" | "completed" | "failed";
  feature?: string;
  action?: string;
  phase?: string;
  completed_units?: number;
  total_units?: number;
  progress_percent?: number;
  error_status?: number;
}

export interface Activity {
  id: string;
  owner: string;
  path?: string;
  state?: JobState;
  result?: { http_status: number; body: unknown };
  error?: string;
  lastPhase?: string;
}

let owner = "";
let snapshot: Activity[] = [];
const empty: Activity[] = [];
const listeners = new Set<() => void>();
const activities = new Map<string, Activity>();
const observers = new Map<string, Promise<Response>>();

export const subscribe = (callback: () => void) => {
  listeners.add(callback);
  return () => { listeners.delete(callback); };
};
export const getSnapshot = () => snapshot;
export const getOwner = () => owner;
export const getServerSnapshot = () => empty;

function publish(activity: Activity) {
  if (activity.owner !== owner) return;
  activities.set(activity.id, activity);
  snapshot = Array.from(activities.values());
  listeners.forEach((callback) => callback());
}

export function setOwner(next: string) {
  if (owner === next) return;
  owner = next;
  activities.clear();
  snapshot = [];
  listeners.forEach((callback) => callback());
}

export function dismiss(id: string) {
  activities.delete(id);
  snapshot = Array.from(activities.values());
  listeners.forEach((callback) => callback());
}

function failure(status?: number) {
  return status === 429 ? "이 체험의 허용된 실행량을 사용했습니다. 다른 기능을 둘러보거나 시작한 체험 결과를 확인해 주세요." : status === 413
    ? "평가할 입력이 너무 큽니다. 입력을 줄여 주세요."
    : "평가 작업에 실패했습니다. 원래 입력 화면에서 확인해 주세요.";
}

async function poll(activity: Activity): Promise<Response> {
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
  const options = { credentials: "include" as const, cache: "no-store" as const };
  const endpoint = `${base}/api/demo/jobs/${activity.id}`;
  try {
    while (true) {
      if (activity.owner !== owner) return new Response(null, { status: 401 });
      const response = await fetch(endpoint, options);
      if (!response.ok) {
        activity.error = response.status === 401 ? "체험 세션이 만료되었습니다. 다시 입장해 주세요."
          : response.status === 404 ? "이 세션에서 작업을 찾을 수 없습니다."
          : "진행 상황을 확인하지 못했습니다. 조회를 다시 연결해 주세요.";
        publish({ ...activity });
        return response;
      }
      const state = await response.json() as JobState;
      if (activity.owner !== owner) return new Response(null, { status: 401 });
      if (!["queued", "running", "completed", "failed"].includes(state.status)) {
        throw new Error("invalid job state");
      }
      activity = { ...activity, state, error: undefined,
        lastPhase: state.phase === "failed" ? activity.state?.phase : state.phase };
      publish(activity);
      if (state.status === "failed") {
        const detail = failure(state.error_status);
        publish({ ...activity, error: detail });
        return new Response(JSON.stringify({ detail }), {
          status: state.error_status ?? 503,
          headers: { "Content-Type": "application/json", "X-Demo-Job-Terminal": "failed" },
        });
      }
      if (state.status === "completed") {
        const resultResponse = await fetch(`${endpoint}/result`, options);
        if (!resultResponse.ok) {
          publish({ ...activity, error: resultResponse.status === 401
            ? "체험 세션이 만료되었습니다. 다시 입장해 주세요."
            : "저장된 결과를 가져오지 못했습니다. 조회를 다시 연결해 주세요." });
          return resultResponse;
        }
        const result = await resultResponse.json() as Activity["result"];
        if (!result || !Number.isInteger(result.http_status) || result.http_status < 200 ||
            result.http_status > 299 || !result.body || typeof result.body !== "object") {
          throw new Error("invalid native result");
        }
        if (activity.owner !== owner) return new Response(null, { status: 401 });
        publish({ ...activity, result });
        return new Response(JSON.stringify(result.body), {
          status: result.http_status, headers: { "Content-Type": "application/json" },
        });
      }
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  } catch {
    publish({ ...activity, error: "연결이 끊겼습니다. 작업은 서버에서 계속될 수 있습니다. 조회를 다시 연결해 주세요." });
    throw new Error("작업 조회 연결이 끊겼습니다. 같은 작업의 조회를 다시 연결해 주세요.");
  }
}

export function observe(id: string, visitor: string, path?: string): Promise<Response> {
  setOwner(visitor);
  const key = `${visitor}:${id}`;
  let running = observers.get(key);
  if (!running) {
    const activity = { id, owner: visitor, path };
    publish(activity);
    running = poll(activity).finally(() => { observers.delete(key); });
    observers.set(key, running);
  }
  return running.then((response) => response.clone());
}

/** Caller cancellation stops waiting, while the shared observer can still display completion. */
export function withSignal<T>(work: Promise<T>, signal?: AbortSignal | null): Promise<T> {
  if (!signal) return work;
  return new Promise((resolve, reject) => {
    const abort = () => reject(new DOMException("Request aborted", "AbortError"));
    if (signal.aborted) abort();
    else signal.addEventListener("abort", abort, { once: true });
    work.then(resolve, reject).finally(() => signal.removeEventListener("abort", abort));
  });
}
