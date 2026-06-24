import { highlight, langForPath } from "./highlight";
import styles from "./workspace.module.css";

export interface ViewFile {
  path: string;
  content: string | null;
}

function langLabel(path: string): string {
  if (path.endsWith(".py")) return "python";
  if (path.endsWith(".ts") || path.endsWith(".tsx")) return "typescript";
  if (path.endsWith(".toml")) return "toml";
  if (path.endsWith(".json")) return "json";
  if (path.endsWith(".md")) return "markdown";
  if (path === "Makefile" || path.endsWith("/Makefile")) return "makefile";
  if (path.includes(".env")) return "dotenv";
  return "text";
}

export function FileWell({ file }: { file: ViewFile | null }) {
  const lines = file?.content != null ? highlight(file.content, langForPath(file.path)) : [];

  return (
    <section className={styles.well} aria-label="파일 내용">
      <header className={styles.wellHead}>
        <span className={styles.kickerLight}>{file ? "FILE · 읽기 전용" : "FILE"}</span>
        {file ? (
          <span className={styles.wellHeadRight}>
            <span className={styles.langTag}>{langLabel(file.path)}</span>
            <span className={styles.pathTag}>{file.path}</span>
          </span>
        ) : null}
      </header>
      {file ? (
        <div className={styles.wellScroll}>
          <div className={styles.gutter} aria-hidden="true">
            {lines.map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>
          <pre className={styles.wellBody}>
            {lines.map((toks, i) => (
              <div key={i} className={styles.wellLine}>
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
        <div className={styles.wellEmpty}>왼쪽 트리에서 파일을 선택하면 내용이 여기에 표시됩니다.</div>
      )}
    </section>
  );
}
