import { CodeMeta, CodePanel } from "@/components/ui/CodePanel";

import { DataTable } from "./DataTable";

type RunResultsProps = {
  /** Columns of the target table, for rendering returned rows. */
  columns: string[];
  rows: Record<string, unknown>[];
  hasRun: boolean;
};

/** The single dark "ink" well: shows the rows the AI returned for the last run.
 *  Deliberately shows NO correctness — the candidate verifies output by eye and
 *  refines the prompt; the score stays hidden until final scoring. */
export function RunResults({ columns, rows, hasRun }: RunResultsProps) {
  return (
    <CodePanel
      label="AI 추출 결과"
      meta={hasRun ? <CodeMeta>{rows.length} 건</CodeMeta> : undefined}
    >
      {!hasRun ? (
        <p className="font-mono text-[13px] text-ink-muted">
          프롬프트를 실행하면 AI가 추출한 행이 여기에 표시됩니다. (정답 여부는 채점 전까지 숨겨집니다)
        </p>
      ) : rows.length === 0 ? (
        <p className="font-mono text-[13px] text-ink-muted">반환된 행이 없습니다.</p>
      ) : (
        <DataTable columns={columns} rows={rows} onDark maxHeightClass="max-h-72" />
      )}
    </CodePanel>
  );
}
