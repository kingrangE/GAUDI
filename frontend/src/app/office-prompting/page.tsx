"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { createSession, runProblem } from "@/features/office-prompting/api";
import { DatasetTables } from "@/features/office-prompting/components/DatasetTables";
import { RunResults } from "@/features/office-prompting/components/RunResults";
import type {
  CreateSessionResponse,
  DatasetTable,
  ProblemMeta,
  RunResponse,
} from "@/features/office-prompting/types";

export default function OfficePromptingPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [session, setSession] = useState<CreateSessionResponse | null>(null);
  const [selected, setSelected] = useState(0);
  const [prompts, setPrompts] = useState<Record<number, string>>({});
  const [runs, setRuns] = useState<Record<number, RunResponse>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const targetColumns = useMemo(() => {
    const target = session?.datasets.find((d) => d.name === "customers");
    return target?.columns ?? [];
  }, [session]);

  async function onStart() {
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setSession(await createSession(name.trim()));
    } catch {
      setError("세션을 시작하지 못했습니다. 백엔드가 실행 중인지 확인하세요.");
    } finally {
      setBusy(false);
    }
  }

  async function onRun() {
    if (!session) return;
    const prompt = (prompts[selected] ?? "").trim();
    if (!prompt) return;
    setBusy(true);
    setError(null);
    try {
      const res = await runProblem(session.session_id, selected, prompt);
      setRuns((prev) => ({ ...prev, [selected]: res }));
    } catch {
      setError("실행에 실패했습니다. 남은 실행 횟수를 확인하세요.");
    } finally {
      setBusy(false);
    }
  }

  function onScore() {
    if (!session) return;
    router.push(`/office-prompting/result/${session.session_id}`);
  }

  // --- entry: collect candidate name ---------------------------------------
  if (!session) {
    return (
      <div className="space-y-4 py-6">
        <div>
          <p className="text-sm font-semibold text-brand-600">사무직 Prompting</p>
          <h1 className="text-xl font-bold text-ink-900">데이터 분석 프롬프팅 평가</h1>
        </div>
        <Panel className="max-w-md space-y-3">
          <SectionLabel>응시자</SectionLabel>
          <p className="text-sm text-ink-soft">
            여러 표(CSV)를 조합해야 풀리는 문제 3개가 주어집니다. 각 문제에서 AI에게
            보낼 프롬프트를 작성해, 조건을 만족하는 고객을 정확히 찾아내세요.
          </p>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="이름"
            className="w-full rounded-md border border-line bg-paper px-3 py-2 text-sm text-ink-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          />
          <Button onClick={onStart} disabled={busy || !name.trim()}>
            {busy ? "준비 중…" : "평가 시작"}
          </Button>
          {error ? <p className="text-sm text-bad-600">{error}</p> : null}
        </Panel>
      </div>
    );
  }

  const problems: ProblemMeta[] = session.problems;
  const problem = problems[selected];
  const datasets: DatasetTable[] = session.datasets;
  const run = runs[selected];
  const runsUsed = run?.runs_used ?? 0;
  const runsRemaining = run ? run.runs_remaining : problem.max_runs;
  const everyProblemRun = problems.every((p) => runs[p.index]);

  return (
    <div className="space-y-4 py-6">
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-brand-600">사무직 Prompting</p>
          <h1 className="text-xl font-bold text-ink-900">데이터 분석 프롬프팅 평가</h1>
        </div>
        <Button variant="secondary" onClick={onScore} disabled={!everyProblemRun}>
          {everyProblemRun ? "제출하고 채점" : "모든 문제를 1회 이상 실행하세요"}
        </Button>
      </div>

      {/* Problem picker */}
      <Panel className="flex flex-wrap items-center gap-2">
        {problems.map((p) => (
          <button
            key={p.index}
            type="button"
            onClick={() => setSelected(p.index)}
            className={
              p.index === selected
                ? "rounded-md bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700"
                : "rounded-md px-3 py-1.5 text-xs font-semibold text-ink-soft hover:bg-paper hover:text-ink-900"
            }
          >
            문제 {p.index + 1}
            {runs[p.index] ? " ✓" : ""}
          </button>
        ))}
      </Panel>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        {/* Left — problem + datasets */}
        <Panel className="h-fit space-y-4">
          <div>
            <SectionLabel>문제 {problem.index + 1}</SectionLabel>
            <h2 className="mt-1 text-lg font-bold text-ink-900">{problem.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">{problem.description}</p>
            <p className="mt-2 text-xs text-ink-faint">
              반환 대상: <span className="font-mono">{problem.target_entity}</span>
            </p>
          </div>
          <DatasetTables datasets={datasets} />
        </Panel>

        {/* Right — prompt editor + AI result */}
        <div className="flex flex-col gap-3">
          <Panel className="flex flex-col">
            <div className="flex items-center justify-between">
              <SectionLabel>INSTRUCT THE AGENT</SectionLabel>
              <Badge tone={runsRemaining > 0 ? "brand" : "bad"}>
                남은 실행 {runsRemaining}/{problem.max_runs}
              </Badge>
            </div>
            <textarea
              value={prompts[selected] ?? ""}
              onChange={(e) => setPrompts((prev) => ({ ...prev, [selected]: e.target.value }))}
              rows={8}
              placeholder="예) orders와 products를 product_id로 조인해 category='가전'인 2024년 7~9월 결제(paid) 주문만 남기고, 해당 고객의 customer_id를 모두 반환해줘."
              className="mt-3 w-full resize-none rounded-lg border border-line p-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
            />
            <div className="mt-3 flex items-center gap-3">
              <Button
                onClick={onRun}
                disabled={busy || runsRemaining <= 0 || !(prompts[selected] ?? "").trim()}
              >
                {busy ? "실행 중…" : `실행 (${runsUsed}/${problem.max_runs})`}
              </Button>
              {runsRemaining <= 0 ? (
                <span className="text-xs text-ink-soft">이 문제의 실행 횟수를 모두 사용했습니다.</span>
              ) : null}
            </div>
          </Panel>

          <RunResults columns={targetColumns} rows={run?.predicted_rows ?? []} hasRun={!!run} />
        </div>
      </div>
      {error ? <p className="text-sm text-bad-600">{error}</p> : null}
    </div>
  );
}
