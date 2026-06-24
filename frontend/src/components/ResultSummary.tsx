import type { ResultResponse } from "../lib/types";

const pct = (n: number): string => `${Math.round(n * 100)}%`;

export function ResultSummary({ result }: { result: ResultResponse }) {
  return (
    <div className="panel">
      <div className="spread">
        <h2>{result.candidate_name} 님의 결과</h2>
        <span className="tag">{result.status}</span>
      </div>
      <div className="row" style={{ gap: "2rem", marginTop: "0.5rem" }}>
        <div>
          <div className="muted">결함 발견율 (Recall)</div>
          <div className="metric">{pct(result.recall)}</div>
        </div>
        <div>
          <div className="muted">정밀도 (Precision)</div>
          <div className="metric">{pct(result.precision)}</div>
        </div>
        <div>
          <div className="muted">가중 점수</div>
          <div className="metric">{pct(result.weighted_score)}</div>
        </div>
      </div>
    </div>
  );
}
