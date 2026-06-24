"use client";

import Link from "next/link";

import { Panel, buttonClasses } from "@/components/ui";

import { useSessionResult } from "../queries";
import { ResultView } from "./ResultView";

/** Result page entry: poll the session until graded, then render the report. */
export function CsEvalResult({ sessionId }: { sessionId: string }) {
  const { data, isPending, isError } = useSessionResult(sessionId);

  if (isPending) return <p className="text-ink-soft">불러오는 중…</p>;
  if (isError || !data) {
    return <p className="text-bad-600">결과를 불러오지 못했습니다.</p>;
  }

  if (data.status === "grading") {
    return (
      <Panel>
        <p className="text-ink-soft">채점 중… 잠시만 기다려 주세요.</p>
      </Panel>
    );
  }

  if (data.status === "failed") {
    return (
      <Panel>
        <p className="text-bad-600">채점에 실패했습니다: {data.error}</p>
        <Link href="/cs-eval" className={buttonClasses("secondary", "mt-3")}>
          ← 다시 풀기
        </Link>
      </Panel>
    );
  }

  return <ResultView result={data} />;
}
