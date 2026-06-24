import { highlightPython, type Tok } from "./highlight";
import { parseContentSegments } from "./sampleContent";
import type { Sample } from "./types";
import styles from "./spec_design.module.css";

function CodeWell({ lang, code }: { lang: string; code: string }) {
  const isPython = lang === "python" || lang === "py" || lang === "";
  const lines = code.split("\n");
  const rows: Tok[][] = isPython
    ? highlightPython(code)
    : lines.map<Tok[]>((line) => [{ t: "txt", v: line }]);

  return (
    <div className={styles.codewell}>
      <div className={styles.codewellHead}>
        <span className={styles.langtag}>{lang || "code"}</span>
      </div>
      <div className={styles.codewellScroll}>
        <div className={styles.gutter} aria-hidden="true">
          {lines.map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>
        <div className={styles.codebody}>
          {rows.map((toks, i) => (
            <div key={i} className={styles.codeline}>
              {toks.length === 0
                ? " "
                : toks.map((tok, j) => (
                    <span key={j} className={styles[`tok_${tok.t}`]}>
                      {tok.v}
                    </span>
                  ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function SampleList({ samples }: { samples: Sample[] }) {
  if (samples.length === 0) {
    return null;
  }
  return (
    <section className={`${styles.card} ${styles.samplesWell}`} aria-label="생성된 샘플">
      <div className={styles.kickerLight}>생성된 샘플 ({samples.length})</div>
      {samples.map((sample) => (
        <details key={sample.index} className={styles.sample} open={sample.index === 0}>
          <summary className={styles.sampleSummary}>샘플 #{sample.index + 1}</summary>
          <div className={styles.sampleBody}>
            {parseContentSegments(sample.content).map((segment, i) =>
              segment.kind === "code" ? (
                <CodeWell key={i} lang={segment.lang} code={segment.code} />
              ) : (
                <p key={i} className={styles.sampleText}>
                  {segment.text}
                </p>
              ),
            )}
          </div>
        </details>
      ))}
    </section>
  );
}
