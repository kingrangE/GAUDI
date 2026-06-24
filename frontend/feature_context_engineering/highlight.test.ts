import { describe, expect, it } from "vitest";

import {
  highlight,
  highlightGeneric,
  highlightMarkdown,
  highlightPython,
  highlightTs,
  langForPath,
} from "./highlight";

describe("langForPath", () => {
  it("maps extensions to languages", () => {
    expect(langForPath("app/main.py")).toBe("python");
    expect(langForPath("README.md")).toBe("markdown");
    expect(langForPath("src/main.tsx")).toBe("ts");
    expect(langForPath("vite.config.ts")).toBe("ts");
    expect(langForPath("pyproject.toml")).toBe("generic");
    expect(langForPath("Makefile")).toBe("generic");
  });
});

describe("highlightPython", () => {
  it("classifies keywords, builtins, strings, numbers, comments", () => {
    const flat = highlightPython('def f():\n    print("hi")  # note\n    return 42').flat();
    const has = (t: string, v: string) => flat.some((tk) => tk.t === t && tk.v === v);
    expect(has("kw", "def")).toBe(true);
    expect(has("bi", "print")).toBe(true);
    expect(has("str", '"hi"')).toBe(true);
    expect(has("num", "42")).toBe(true);
    expect(flat.some((tk) => tk.t === "com" && tk.v.includes("# note"))).toBe(true);
  });

  it("emits one token list per line and preserves text via concatenation", () => {
    const lines = highlightPython("from app import x\ny = 1");
    expect(lines).toHaveLength(2);
    expect(lines[0].map((t) => t.v).join("")).toBe("from app import x");
  });
});

describe("highlightGeneric", () => {
  it("highlights comments, strings and standalone numbers", () => {
    const flat = highlightGeneric('name = "todo"  # c\nport = 8000').flat();
    const has = (t: string, v: string) => flat.some((tk) => tk.t === t && tk.v === v);
    expect(has("str", '"todo"')).toBe(true);
    expect(has("num", "8000")).toBe(true);
    expect(flat.some((tk) => tk.t === "com" && tk.v.includes("# c"))).toBe(true);
  });

  it("does not split digits inside identifiers", () => {
    expect(highlightGeneric("psycopg2").flat().every((tk) => tk.t !== "num")).toBe(true);
  });
});

describe("highlightMarkdown", () => {
  it("treats headings as one keyword token and inline code as strings", () => {
    const lines = highlightMarkdown("# Title\nrun `make test` now");
    expect(lines[0]).toEqual([{ t: "kw", v: "# Title" }]);
    expect(lines[1].some((tk) => tk.t === "str" && tk.v === "`make test`")).toBe(true);
  });
});

describe("highlightTs", () => {
  it("classifies // comments, strings, keywords, and builtins", () => {
    const flat = highlightTs('const x = "a"; // c\nconsole.log(x)').flat();
    const has = (t: string, v: string) => flat.some((tk) => tk.t === t && tk.v === v);
    expect(has("kw", "const")).toBe(true);
    expect(has("str", '"a"')).toBe(true);
    expect(has("bi", "console")).toBe(true);
    expect(flat.some((tk) => tk.t === "com" && tk.v.includes("// c"))).toBe(true);
  });

  it("keeps an unterminated block comment as one comment run across lines", () => {
    const lines = highlightTs("/* start\nmiddle\nend */ const x = 1");
    expect(lines[1].every((tk) => tk.t === "com")).toBe(true);
  });
});

describe("highlight dispatcher", () => {
  it("routes by language", () => {
    expect(highlight("# h\n", "markdown")[0][0].t).toBe("kw");
    expect(highlight("x = 1", "python").flat().some((t) => t.t === "num")).toBe(true);
    expect(highlight('const a = 1', "ts").flat().some((t) => t.t === "kw")).toBe(true);
  });
});
