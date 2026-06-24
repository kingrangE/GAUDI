"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";

import { isTerminal, useProblem, useRunMutation, useSubmitAndPoll } from "../queries";
import { ProblemPane } from "./ProblemPane";
import { ResultCards } from "./ResultCards";
import { RunResults } from "./RunResults";

// CodeMirror is client-only — load it without SSR.
const CodeEditor = dynamic(() => import("./CodeEditor"), {
  ssr: false,
  loading: () => <p className="p-4 text-sm text-slate-500">에디터 로딩…</p>,
});

const TIMER_SECONDS = 30 * 60;
const DEFAULT_CANDIDATE = "demo-candidate";

export function SolvePanel({ problemId }: { problemId: string }) {
  const problemQuery = useProblem(problemId);
  const [code, setCode] = useState("");
  const [candidateId] = useState(DEFAULT_CANDIDATE);

  useEffect(() => {
    if (problemQuery.data) setCode(problemQuery.data.starter_code);
  }, [problemQuery.data]);

  const run = useRunMutation(problemId);
  const { submit, result, submissionId } = useSubmitAndPoll(problemId, candidateId);

  if (problemQuery.isPending) return <p className="p-8">불러오는 중…</p>;
  if (problemQuery.isError || !problemQuery.data) {
    return <p className="p-8 text-red-600">문제를 불러오지 못했습니다.</p>;
  }

  const grading =
    submit.isPending || (Boolean(submissionId) && !isTerminal(result.data?.status));

  return (
    <main className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b bg-white px-4 py-2">
        <Link href="/coding-test" className="text-sm text-slate-500 hover:underline">
          ← 목록
        </Link>
      </header>
      <div className="grid flex-1 grid-cols-2 overflow-hidden">
        <section className="overflow-y-auto border-r bg-white">
          <ProblemPane problem={problemQuery.data} timerSeconds={TIMER_SECONDS} />
        </section>
        <section className="flex flex-col overflow-hidden">
          <div className="min-h-0 flex-1 overflow-auto border-b">
            <CodeEditor value={code} onChange={setCode} />
          </div>
          <div className="flex gap-2 border-b bg-white p-2">
            <button
              onClick={() => run.mutate(code)}
              disabled={run.isPending}
              className="rounded border px-3 py-1 text-sm disabled:opacity-50"
            >
              실행
            </button>
            <button
              onClick={() => submit.mutate(code)}
              disabled={submit.isPending}
              className="rounded bg-slate-900 px-3 py-1 text-sm text-white disabled:opacity-50"
            >
              제출
            </button>
          </div>
          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto bg-slate-50 p-4">
            <RunResults data={run.data} isPending={run.isPending} />
            <ResultCards result={result.data} isPending={grading} />
          </div>
        </section>
      </div>
    </main>
  );
}
