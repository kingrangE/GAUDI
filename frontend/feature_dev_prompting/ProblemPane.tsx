import type { Example, ProblemPublic } from "./types";
import styles from "./workspace.module.css";

function paramNames(starter: string): string[] {
  const m = starter.match(/def\s+\w+\s*\(([^)]*)\)/);
  if (!m) {
    return [];
  }
  return m[1]
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function formatInput(names: string[], ex: Example): string {
  if (names.length === ex.args.length) {
    return ex.args.map((a, i) => `${names[i]} = ${JSON.stringify(a)}`).join(", ");
  }
  return ex.args.map((a) => JSON.stringify(a)).join(", ");
}

export function ProblemPane({ problem }: { problem: ProblemPublic }) {
  const names = paramNames(problem.starter_code);
  return (
    <section className={styles.problem} aria-label="문제">
      <div className={styles.kicker}>PROBLEM · {problem.id}</div>
      <h1 className={styles.problemTitle}>{problem.title}</h1>
      <div className={styles.meta}>
        <span>제한 {problem.time_limit_sec}s</span>
        <span>예제 {problem.public_example_count}</span>
        <span>함수 {problem.entry_point}</span>
      </div>
      <p className={styles.statement}>{problem.statement}</p>

      {problem.examples.length > 0 ? (
        <div className={styles.examples}>
          <div className={styles.kicker}>입출력 예</div>
          {problem.examples.map((ex, i) => (
            <div key={i} className={styles.exampleCard}>
              <div className={styles.exampleNo}>예시 {i + 1}</div>
              <div className={styles.exampleRow}>
                <span className={styles.exampleLabel}>입력</span>
                <code className={styles.exampleVal}>{formatInput(names, ex)}</code>
              </div>
              <div className={styles.exampleRow}>
                <span className={styles.exampleLabel}>출력</span>
                <code className={styles.exampleVal}>{JSON.stringify(ex.expected)}</code>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {problem.constraints ? (
        <div className={styles.constraints}>
          <div className={styles.kicker}>CONSTRAINTS</div>
          <pre>{problem.constraints}</pre>
        </div>
      ) : null}
    </section>
  );
}
