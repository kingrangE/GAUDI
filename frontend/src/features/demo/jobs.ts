interface PendingJob {
  key: string;
  jobId?: string;
}

const memory = new Map<string, PendingJob>();

function read(key: string): PendingJob | undefined {
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const value = JSON.parse(raw) as PendingJob;
      if (typeof value.key === "string" &&
          (value.jobId === undefined || /^[a-f0-9]{32}$/.test(value.jobId))) return value;
    }
  } catch { /* Memory keeps retries safe when persistent storage is unavailable. */ }
  return memory.get(key);
}

function save(key: string, value?: PendingJob): void {
  if (value) memory.set(key, value);
  else memory.delete(key);
  try {
    if (value) localStorage.setItem(key, JSON.stringify(value));
    else localStorage.removeItem(key);
  } catch { /* The current document can continue through the memory fallback. */ }
}

async function pause(signal?: AbortSignal | null): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const stop = () => {
      clearTimeout(timer);
      reject(new DOMException("Request aborted", "AbortError"));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", stop);
      resolve();
    }, 1000);
    if (signal?.aborted) stop();
    else signal?.addEventListener("abort", stop, { once: true });
  });
}

/** Preserve the native response contract while the server executes a durable job. */
export async function queuedFetch(url: string, init: RequestInit, owner: string): Promise<Response> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(
    JSON.stringify([url, init.body ?? ""]),
  ));
  const fingerprint = Array.from(new Uint8Array(digest), (n) => n.toString(16).padStart(2, "0")).join("");
  const storageKey = `gaudi:pending-job:${owner}:${fingerprint}`;
  const pending = read(storageKey) ?? { key: crypto.randomUUID() };
  save(storageKey, pending);
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
  const request = { credentials: "include" as const, signal: init.signal, cache: "no-store" as const };

  if (!pending.jobId) {
    const headers = new Headers(init.headers);
    headers.set("Idempotency-Key", pending.key);
    const response = await fetch(url, { ...init, headers });
    if (!response.ok) {
      if (response.status >= 400 && response.status < 500 && response.status !== 429) save(storageKey);
      return response;
    }
    if (response.status !== 202) throw new Error("평가 작업 접수 응답을 확인하지 못했습니다.");
    const accepted = await response.json() as { job_id: string };
    if (!/^[a-f0-9]{32}$/.test(accepted.job_id)) throw new Error("평가 작업 ID가 올바르지 않습니다.");
    pending.jobId = accepted.job_id;
    save(storageKey, pending);
  }

  while (true) {
    const stateResponse = await fetch(`${base}/api/demo/jobs/${pending.jobId}`, request);
    if (!stateResponse.ok) return stateResponse;
    const state = await stateResponse.json() as { status: string; error_status?: number };
    if (state.status === "failed") {
      save(storageKey);
      const detail = state.error_status === 429
        ? "이 체험의 허용된 실행량을 사용했습니다. 다른 기능을 둘러보거나 시작한 체험 결과를 확인해 주세요."
        : state.error_status === 413
          ? "평가할 입력이 너무 큽니다. 입력을 줄여 주세요."
          : "평가 작업에 실패했습니다. 입력을 확인해 주세요.";
      return new Response(JSON.stringify({ detail }), {
        status: state.error_status ?? 503, headers: { "Content-Type": "application/json" },
      });
    }
    if (state.status === "completed") {
      const resultResponse = await fetch(`${base}/api/demo/jobs/${pending.jobId}/result`, request);
      if (!resultResponse.ok) return resultResponse;
      const result = await resultResponse.json() as { http_status: number; body: unknown };
      if (!Number.isInteger(result.http_status) || result.http_status < 200 || result.http_status > 299) {
        throw new Error("평가 결과 응답이 올바르지 않습니다.");
      }
      save(storageKey);
      return new Response(JSON.stringify(result.body), {
        status: result.http_status, headers: { "Content-Type": "application/json" },
      });
    }
    await pause(init.signal);
  }
}
