import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { Activity } from "./tracking";
import { JobActivity } from "./JobActivity";
import { recoverPending } from "./jobs";
import { dismiss, observe } from "./tracking";

const store = vi.hoisted(() => ({ jobs: [] as Activity[], listeners: new Set<() => void>() }));
vi.mock("./tracking", () => ({
  subscribe: (callback: () => void) => { store.listeners.add(callback); return () => store.listeners.delete(callback); },
  getSnapshot: () => store.jobs, getServerSnapshot: () => store.jobs, getOwner: () => "",
  observe: vi.fn().mockResolvedValue(new Response()), dismiss: vi.fn(),
}));
vi.mock("./jobs", () => ({ recoverPending: vi.fn().mockResolvedValue(undefined) }));

const owner = "b".repeat(32);
const initial: Activity = { id: "a".repeat(32), owner, state: {
  feature: "context_engineering", action: "post_submission", status: "queued", phase: "queued",
  completed_units: 0, total_units: 4,
} };

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_DEMO_ENABLED", "true");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 401 })));
  store.jobs = [initial];
});
afterEach(() => { cleanup(); vi.clearAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
async function show() {
  let view!: ReturnType<typeof render>;
  await act(async () => {
    view = render(<QueryClientProvider client={new QueryClient()}><JobActivity /></QueryClientProvider>);
  });
  return view;
}
function publish(job: Activity) { act(() => { store.jobs = [job]; store.listeners.forEach((listener) => listener()); }); }

it("shows a clearly separate fictional report while queued, without fake percentages", async () => {
  await show();
  expect(screen.getByText("미리 작성한 합성 예시")).toBeTruthy();
  expect(screen.getByText(/현재 문제의 정답이나 이번 입력의 평가 결과가 아닙니다/)).toBeTruthy();
  expect(screen.getByText("실행 순서를 기다리는 중")).toBeTruthy();
  expect(screen.getByRole("progressbar").hasAttribute("aria-valuenow")).toBe(false);
  expect(screen.queryByText("Live Report")).toBeNull();
});

it("transitions to real report and 100% only after result retrieval", async () => {
  await show();
  publish({ ...initial, state: { ...initial.state!, status: "running", completed_units: 4, total_units: 4 } });
  expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("99");
  publish({ ...initial, state: { ...initial.state!, status: "completed", completed_units: 4, total_units: 4 } });
  expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("99");
  expect(screen.queryByText("Live Report")).toBeNull();
  publish({ ...initial, state: { ...initial.state!, status: "completed" }, result: {
    http_status: 201, body: { total: 71, dimensions: [], results: [] },
  } });
  expect(screen.getByText("Live Report")).toBeTruthy();
  expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("100");
  expect(screen.getByText("71")).toBeTruthy();
  expect(screen.queryByText("미리 작성한 합성 예시")).toBeNull();
});

it("lets visitors browse while work continues and reconnect without new evaluation", async () => {
  await show();
  fireEvent.click(screen.getByRole("button", { name: "접어두고 둘러보기" }));
  expect(screen.queryByRole("progressbar")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "작업 현황 펼치기" }));
  publish({ ...initial, error: "연결을 확인해 주세요." });
  fireEvent.click(screen.getByRole("button", { name: "조회 다시 연결" }));
  expect(observe).toHaveBeenCalledWith(initial.id, owner, undefined);
});

it("keeps terminal failure separate from sample output and never auto-retries evaluation", async () => {
  store.jobs = [{ ...initial, state: { ...initial.state!, status: "failed" }, error: "평가 실패" }];
  await show();
  expect(screen.getByRole("alert").textContent).toBe("평가 실패");
  expect(screen.getByText("미리 작성한 합성 예시")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "조회 다시 연결" })).toBeNull();
  expect(observe).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "닫기" }));
  expect(dismiss).toHaveBeenCalledWith(initial.id);
});

it("automatically restores owned job IDs from a read-only session lookup", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ session_id: owner }))));
  await show();
  await vi.waitFor(() => expect(recoverPending).toHaveBeenCalledWith(owner));
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/demo/session"), {
    credentials: "include", cache: "no-store",
  });
});

it("does not change the ordinary non-demo flow", async () => {
  vi.stubEnv("NEXT_PUBLIC_DEMO_ENABLED", "false");
  const { container } = await show();
  expect(container.textContent).toBe("");
  expect(fetch).not.toHaveBeenCalled();
});

it("can retry initial recovery when the session lookup was offline", async () => {
  store.jobs = [];
  vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce(new TypeError("offline"))
    .mockResolvedValueOnce(new Response(JSON.stringify({ session_id: owner }))));
  await show();
  const retry = await screen.findByRole("button", { name: "이전 작업 다시 확인" });
  await act(async () => { fireEvent.click(retry); });
  await vi.waitFor(() => expect(recoverPending).toHaveBeenCalledWith(owner));
});

it("returns setup results to the original flow without retaining an empty report card", async () => {
  store.jobs = [{ ...initial, state: { ...initial.state!, feature: "office_prompting", action: "create_session", status: "completed" },
    result: { http_status: 201, body: { session_id: "native" } } }];
  const { container } = await show();
  expect(container.textContent).toBe("");
});
