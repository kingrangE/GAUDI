import { useState } from "react";

import styles from "./workspace.module.css";
import type { EvaluationReport } from "./types";

export type SubmitStatus = "idle" | "submitting" | "done" | "error";

interface ContextPaneProps {
  onSubmit: (claudeMd: string) => void;
  status: SubmitStatus;
  report: EvaluationReport | null;
}

export function ContextPane({ onSubmit, status, report }: ContextPaneProps) {
  const [draft, setDraft] = useState("");
  const canSubmit = draft.trim().length > 0 && status !== "submitting";

  function submit() {
    if (!canSubmit) {
      return;
    }
    onSubmit(draft.trim());
  }

  return (
    <section className={styles.console} aria-label="CLAUDE.md 작성">
      <div className={styles.kicker}>AUTHOR CLAUDE.md</div>
      <textarea
        className={styles.editor}
        placeholder="이 프로젝트에서 에이전트가 효율적으로 작업하도록 컨텍스트를 작성하세요. (⌘/Ctrl+Enter로 제출)"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
            submit();
          }
        }}
        disabled={status === "submitting"}
      />
      <button className={styles.submit} onClick={submit} disabled={!canSubmit}>
        {status === "submitting" ? "채점 중…" : "제출"}
      </button>

      {status === "error" ? (
        <div className={styles.error}>제출에 실패했습니다. 백엔드 연결을 확인하세요.</div>
      ) : null}

      {report ? (
        <div className={styles.report} aria-label="평가 결과">
          <div className={styles.scoreRow}>
            <span className={styles.scoreBig}>{report.total}</span>
            <span className={styles.scoreSub}>/ 100 종합</span>
          </div>
          <div className={styles.kicker}>평가 축</div>
          <ul className={styles.dimList}>
            {report.dimensions.map((d) => (
              <li key={d.key} className={styles.dimRow} data-available={d.available}>
                <span className={styles.dimLabel}>{d.label}</span>
                <span className={styles.dimScore}>{d.available ? d.score : "미채점"}</span>
                <span className={styles.dimDetail}>{d.detail}</span>
              </li>
            ))}
          </ul>
          {report.results.length > 0 ? (
            <>
              <div className={styles.kicker}>커버리지 상세</div>
              <ul className={styles.ledger}>
                {report.results.map((r) => (
                  <li key={r.id} className={styles.critRow} data-covered={r.covered}>
                    <span className={styles.critMark}>{r.covered ? "충족" : "누락"}</span>
                    <span className={styles.critText}>{r.text}</span>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </div>
      ) : null}

      <p className={styles.note}>
        채점은 제출한 CLAUDE.md를 이 프로젝트의 ground-truth 체크리스트에 대고 LLM이 항목별로
        판정합니다(포함된 근거를 문서에서 인용). 표현·구조는 자유입니다.
      </p>
    </section>
  );
}
