// Dependency-free, best-effort syntax highlighting for read-only file display.
// Python gets a real tokenizer; Markdown gets heading/inline-code treatment; everything
// else uses a generic comment/string/number pass. Not a full parser.

export type TokType = "kw" | "bi" | "str" | "num" | "com" | "txt";

export interface Tok {
  t: TokType;
  v: string;
}

export type Lang = "python" | "markdown" | "ts" | "generic";

export function langForPath(path: string): Lang {
  if (path.endsWith(".py")) return "python";
  if (path.endsWith(".md")) return "markdown";
  if (/\.(tsx?|jsx?|mjs|cjs)$/.test(path)) return "ts";
  return "generic";
}

export function highlight(code: string, lang: Lang): Tok[][] {
  if (lang === "python") return highlightPython(code);
  if (lang === "markdown") return highlightMarkdown(code);
  if (lang === "ts") return highlightTs(code);
  return highlightGeneric(code);
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
  "bool", "any", "all", "reversed", "round", "ord", "chr", "isinstance", "type", "super",
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

/** Generic comment(#)/string/number pass for config-ish files (toml, make, env, json). */
export function highlightGeneric(code: string): Tok[][] {
  const out: Tok[][] = [];

  for (const line of code.split("\n")) {
    const toks: Tok[] = [];
    const n = line.length;
    let i = 0;
    let txtStart = 0;
    const flush = (end: number) => {
      if (end > txtStart) {
        toks.push({ t: "txt", v: line.slice(txtStart, end) });
      }
    };

    while (i < n) {
      const c = line[i];

      if (c === "#") {
        flush(i);
        toks.push({ t: "com", v: line.slice(i) });
        i = n;
        txtStart = n;
        break;
      }

      if (c === '"' || c === "'") {
        flush(i);
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
        txtStart = j;
        continue;
      }

      const prev = i > 0 ? line[i - 1] : " ";
      if (c >= "0" && c <= "9" && !IDENT_CHAR.test(prev)) {
        flush(i);
        let j = i + 1;
        while (j < n && /[0-9._]/.test(line[j])) {
          j += 1;
        }
        toks.push({ t: "num", v: line.slice(i, j) });
        i = j;
        txtStart = j;
        continue;
      }

      i += 1;
    }

    flush(n);
    out.push(toks);
  }

  return out;
}

/** Markdown: headings as keywords, inline `code` as strings, the rest plain. */
export function highlightMarkdown(code: string): Tok[][] {
  const out: Tok[][] = [];

  for (const line of code.split("\n")) {
    if (/^#{1,6}\s/.test(line)) {
      out.push([{ t: "kw", v: line }]);
      continue;
    }

    const toks: Tok[] = [];
    const n = line.length;
    let i = 0;
    let txtStart = 0;
    const flush = (end: number) => {
      if (end > txtStart) {
        toks.push({ t: "txt", v: line.slice(txtStart, end) });
      }
    };

    while (i < n) {
      if (line[i] === "`") {
        const close = line.indexOf("`", i + 1);
        if (close === -1) {
          break;
        }
        flush(i);
        toks.push({ t: "str", v: line.slice(i, close + 1) });
        i = close + 1;
        txtStart = i;
        continue;
      }
      i += 1;
    }

    flush(n);
    out.push(toks);
  }

  return out;
}

const TS_KEYWORDS = new Set([
  "abstract", "as", "async", "await", "break", "case", "catch", "class", "const",
  "continue", "default", "delete", "do", "else", "enum", "export", "extends", "false",
  "finally", "for", "from", "function", "if", "implements", "import", "in", "instanceof",
  "interface", "let", "new", "null", "of", "private", "protected", "public", "readonly",
  "return", "static", "super", "switch", "this", "throw", "true", "try", "type", "typeof",
  "undefined", "var", "void", "while", "yield",
]);

const TS_BUILTINS = new Set([
  "console", "document", "window", "Math", "JSON", "Date", "Promise", "Array", "Object",
  "String", "Number", "Boolean", "Map", "Set", "Symbol",
]);

const TS_SIGNIFICANT = /[/"'`A-Za-z0-9_]/;

// Best-effort TS/JS tokenizer: line and block comments, strings, numbers, keywords.
export function highlightTs(code: string): Tok[][] {
  const out: Tok[][] = [];
  let block = false; // inside a /* ... */ comment spanning lines

  for (const line of code.split("\n")) {
    const toks: Tok[] = [];
    const n = line.length;
    let i = 0;

    if (block) {
      const close = line.indexOf("*/");
      if (close === -1) {
        toks.push({ t: "com", v: line });
        out.push(toks);
        continue;
      }
      toks.push({ t: "com", v: line.slice(0, close + 2) });
      i = close + 2;
      block = false;
    }

    while (i < n) {
      const c = line[i];

      if (c === "/" && line[i + 1] === "/") {
        toks.push({ t: "com", v: line.slice(i) });
        break;
      }

      if (c === "/" && line[i + 1] === "*") {
        const close = line.indexOf("*/", i + 2);
        if (close === -1) {
          toks.push({ t: "com", v: line.slice(i) });
          block = true;
          break;
        }
        toks.push({ t: "com", v: line.slice(i, close + 2) });
        i = close + 2;
        continue;
      }

      if (c === '"' || c === "'" || c === "`") {
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
        while (j < n && /[0-9._eExXa-fA-F]/.test(line[j])) {
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
        const t: TokType = TS_KEYWORDS.has(word) ? "kw" : TS_BUILTINS.has(word) ? "bi" : "txt";
        toks.push({ t, v: word });
        i = j;
        continue;
      }

      let j = i + 1;
      while (j < n && !TS_SIGNIFICANT.test(line[j])) {
        j += 1;
      }
      toks.push({ t: "txt", v: line.slice(i, j) });
      i = j;
    }

    out.push(toks);
  }

  return out;
}
