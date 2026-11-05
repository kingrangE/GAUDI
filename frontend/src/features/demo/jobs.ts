import { getOwner, observe, setOwner, withSignal } from "./tracking";

interface PendingJob {
  key: string;
  jobId?: string;
  path?: string;
}

const memory = new Map<string, PendingJob>();
const SETUP_PATHS = new Set(["/test-design/sessions", "/api/office-prompting/sessions",
  "/api/rejection-eval/sessions", "/dev-prompting/runs"]);

function read(key: string): PendingJob | undefined {
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const value = JSON.parse(raw) as PendingJob;
      if (typeof value.key === "string" &&
          (value.jobId === undefined || /^[a-f0-9]{32}$/.test(value.jobId))) {
        return { key: value.key, jobId: value.jobId,
          path: typeof value.path === "string" && value.path.startsWith("/") ? value.path : undefined };
      }
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

/** Preserve the native response contract while the server executes a durable job. */
export async function queuedFetch(url: string, init: RequestInit, owner: string): Promise<Response> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(
    JSON.stringify([url, init.body ?? ""]),
  ));
  const fingerprint = Array.from(new Uint8Array(digest), (n) => n.toString(16).padStart(2, "0")).join("");
  const storageKey = `gaudi:pending-job:${owner}:${fingerprint}`;
  const path = new URL(url, window.location.origin).pathname;
  const setup = SETUP_PATHS.has(path);
  const resourceKey = `gaudi:resource-job:${owner}:${fingerprint}`;
  const pending = read(storageKey) ?? (setup ? read(resourceKey) : undefined) ?? { key: crypto.randomUUID() };
  save(storageKey, pending);
  setOwner(owner);

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
    pending.path = path;
    save(storageKey, pending);
  }

  if (getOwner() !== owner) return new Response(null, { status: 401 });
  const work = observe(pending.jobId, owner, pending.path).then((response) => {
    if (response.ok || response.headers.get("X-Demo-Job-Terminal") === "failed") {
      if (setup) save(resourceKey, response.ok ? pending : undefined);
      save(storageKey);
    }
    if (response.status === 401 || response.status === 404) {
      save(resourceKey);
      save(storageKey);
    }
    return response;
  });
  return withSignal(work, init.signal);
}

export async function recoverPending(owner: string): Promise<void> {
  setOwner(owner);
  const keys = new Set(memory.keys());
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) keys.add(key);
    }
  } catch { /* Reconnect in-memory jobs when storage is unavailable. */ }
  await Promise.allSettled(Array.from(keys).filter((key) =>
    key.startsWith(`gaudi:pending-job:${owner}:`),
  ).map(async (key) => {
    const pending = read(key);
    if (!pending?.jobId) return;
    const response = await observe(pending.jobId, owner, pending.path);
    if (response.ok && pending.path && SETUP_PATHS.has(pending.path)) {
      save(key.replace("gaudi:pending-job:", "gaudi:resource-job:"), pending);
    }
    if (response.ok || response.status === 401 || response.status === 404 ||
        response.headers.get("X-Demo-Job-Terminal") === "failed") save(key);
  }));
}
