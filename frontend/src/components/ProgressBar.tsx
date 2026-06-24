export function ProgressBar({ current, total }: { current: number; total: number }) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;
  return (
    <div>
      <div className="spread">
        <span className="muted">
          진행 {current} / {total}
        </span>
        <span className="muted">{pct}%</span>
      </div>
      <div
        style={{
          height: 8,
          background: "var(--panel-2)",
          borderRadius: 999,
          overflow: "hidden",
          marginTop: 4,
        }}
      >
        <div style={{ width: `${pct}%`, height: "100%", background: "var(--accent)" }} />
      </div>
    </div>
  );
}
