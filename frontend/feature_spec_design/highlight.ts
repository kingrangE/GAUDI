// Tiny dependency-free Python tokenizer for read-only code display.
// Best-effort (keywords / builtins / strings / numbers / comments); not a full parser.

export type TokType = "kw" | "bi" | "str" | "num" | "com" | "txt";

export interface Tok {
  t: TokType;
  v: string;
}

const KEYWORDS = new Set([
  "False", "None", "True", "and", "as", "assert", "async", "await", "break", "class",
  "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global",
  "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
  "try", "while", "with", "yield", "match", "case",
]);

const BUILTINS = new Set([
  "print", "len", "range", "int", "str", "float", "list", "dict", "set", "tuple", "map",
  "filter", "sum", "min", "max", "abs", "sorted", "input", "enumerate", "zip", "open",
  "bool", "any", "all", "reversed", "round", "ord", "chr", "isinstance", "type",
]);

const IDENT_START = /[A-Za-z_]/;
const IDENT_CHAR = /[A-Za-z0-9_]/;
const NUM_CHAR = /[0-9._eExXoObBa-fA-F]/;
const SIGNIFICANT = /[#"'A-Za-z0-9_]/;

/** Tokenize Python source into one token list per source line. */
export function highlightPython(code: string): Tok[][] {
  const out: Tok[][] = [];
  let triple: string | null = null; // active triple-quote delimiter spanning lines

  for (const line of code.split("\n")) {
    const toks: Tok[] = [];
    const n = line.length;
    let i = 0;

    if (triple) {
      const close = line.indexOf(triple);
      if (close === -1) {
        toks.push({ t: "str", v: line });
        out.push(toks);
        continue;
      }
      toks.push({ t: "str", v: line.slice(0, close + 3) });
      i = close + 3;
      triple = null;
    }

    while (i < n) {
      const c = line[i];

      if (c === "#") {
        toks.push({ t: "com", v: line.slice(i) });
        break;
      }

      if (c === '"' || c === "'") {
        if (line.slice(i, i + 3) === c + c + c) {
          const close = line.indexOf(c + c + c, i + 3);
          if (close === -1) {
            toks.push({ t: "str", v: line.slice(i) });
            triple = c + c + c;
            break;
          }
          toks.push({ t: "str", v: line.slice(i, close + 3) });
          i = close + 3;
          continue;
        }
        let j = i + 1;
        while (j < n) {
          if (line[j] === "\\") {
            j += 2;
            continue;
          }
          if (line[j] === c) {
            j += 1;
            break;
          }
          j += 1;
        }
        toks.push({ t: "str", v: line.slice(i, j) });
        i = j;
        continue;
      }

      if (c >= "0" && c <= "9") {
        let j = i + 1;
        while (j < n && NUM_CHAR.test(line[j])) {
          j += 1;
        }
        toks.push({ t: "num", v: line.slice(i, j) });
        i = j;
        continue;
      }

      if (IDENT_START.test(c)) {
        let j = i + 1;
        while (j < n && IDENT_CHAR.test(line[j])) {
          j += 1;
        }
        const word = line.slice(i, j);
        const t: TokType = KEYWORDS.has(word) ? "kw" : BUILTINS.has(word) ? "bi" : "txt";
        toks.push({ t, v: word });
        i = j;
        continue;
      }

      let j = i + 1;
      while (j < n && !SIGNIFICANT.test(line[j])) {
        j += 1;
      }
      toks.push({ t: "txt", v: line.slice(i, j) });
      i = j;
    }

    out.push(toks);
  }

  return out;
}
