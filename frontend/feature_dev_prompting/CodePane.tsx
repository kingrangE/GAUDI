import { highlightPython } from "./highlight";
import styles from "./workspace.module.css";

interface CodePaneProps {
  // The starter stub initially; the agent's code after a turn runs.
  code: string | null;
  turn: number | null;
}

export function CodePane({ code, turn }: CodePaneProps) {
  const lines = code ? highlightPython(code) : [];
  const kicker = turn !== null ? "AGENT OUTPUT · 읽기 전용" : "SOLUTION · 읽기 전용";
  return (
    <section className={styles.code} aria-label="에이전트 코드">
      <header className={styles.codeHead}>
        <span className={styles.kickerLight}>{kicker}</span>
        <span className={styles.codeHeadRight}>
          <span className={styles.langTag}>python</span>
          {turn !== null ? (
            <span className={styles.turnTag}>TURN {turn}</span>
          ) : (
            <span className={styles.starterTag}>STARTER</span>
          )}
        </span>
      </header>
      {code ? (
        <div className={styles.codeScroll}>
          <div className={styles.gutter} aria-hidden="true">
            {lines.map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>
          <pre className={styles.codeBody}>
            {lines.map((toks, i) => (
              <div key={i} className={styles.codeLine}>
                {toks.length === 0 ? (
                  <span> </span>
                ) : (
                  toks.map((tk, j) => (
                    <span key={j} className={styles[`tok_${tk.t}`]}>
                      {tk.v}
                    </span>
                  ))
                )}
              </div>
            ))}
          </pre>
        </div>
      ) : (
        <div className={styles.codeEmpty}>표시할 코드가 없습니다.</div>
      )}
    </section>
  );
}
