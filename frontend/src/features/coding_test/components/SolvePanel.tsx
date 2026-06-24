"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { CodeMeta, CodePanel } from "@/components/ui/CodePanel";
import { Panel } from "@/components/ui/Panel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { isTerminal, useProblem, useRunMutation, useSubmitAndPoll } from "../queries";
import { ProblemPane } from "./ProblemPane";
import { ResultCards } from "./ResultCards";
import { RunResults } from "./RunResults";

// CodeMirror is client-only — load it without SSR.
const CodeEditor = dynamic(() => import("./CodeEditor"), {
  ssr: false,
  loading: () => <p className="p-4 text-sm text-ink-muted">에디터 로딩…</p>,
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

  if (problemQuery.isPending) return <p className="py-12 text-center text-slate-500">불러오는 중…</p>;
  if (problemQuery.isError || !problemQuery.data) {
    return <p className="py-12 text-center text-bad-600">문제를 불러오지 못했습니다.</p>;
  }

  const grading =
    submit.isPending || (Boolean(submissionId) && !isTerminal(result.data?.status));

  return (
    <div className="space-y-4">
      <Link href="/coding-test" className="text-sm text-slate-500 hover:text-slate-800">
        ← 문제 목록
      </Link>

      <div className="grid h-[calc(100vh-9.5rem)] grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)_minmax(0,1fr)] gap-4">
        {/* Left — problem */}
        <Panel className="min-h-0 overflow-hidden">
          <ProblemPane problem={problemQuery.data} timerSeconds={TIMER_SECONDS} />
        </Panel>

        {/* Center — code editor (dark) */}
        <CodePanel
          label="내 코드"
          meta={<CodeMeta>python</CodeMeta>}
          flushBody
          className="min-h-[320px]"
        >
          <CodeEditor value={code} onChange={setCode} />
        </CodePanel>

        {/* Right — run / grade */}
        <Panel className="flex min-h-0 flex-col">
          <SectionLabel>실행 &amp; 채점</SectionLabel>
          <div className="mt-3 flex gap-2">
            <Button onClick={() => run.mutate(code)} disabled={run.isPending}>
              실행
            </Button>
            <Button variant="secondary" onClick={() => submit.mutate(code)} disabled={submit.isPending}>
              제출
            </Button>
          </div>
          <div className="mt-4 min-h-0 flex-1 space-y-4 overflow-y-auto">
            <RunResults data={run.data} isPending={run.isPending} />
            <ResultCards result={result.data} isPending={grading} />
          </div>
        </Panel>
      </div>
    </div>
  );
}
