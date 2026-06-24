import { describe, expect, it } from "vitest";

import { highlightPython } from "./highlight";

describe("highlightPython", () => {
  it("classifies keywords, builtins, strings, numbers, and comments", () => {
    const lines = highlightPython('def f():\n    print("hi")  # note\n    return 42');
    const flat = lines.flat();
    const has = (t: string, v: string) => flat.some((tk) => tk.t === t && tk.v === v);

    expect(has("kw", "def")).toBe(true);
    expect(has("bi", "print")).toBe(true);
    expect(has("str", '"hi"')).toBe(true);
    expect(has("num", "42")).toBe(true);
    expect(lines[1].some((tk) => tk.t === "com" && tk.v.includes("# note"))).toBe(true);
  });

  it("emits exactly one token list per source line", () => {
    expect(highlightPython("a\nb\nc")).toHaveLength(3);
  });

  it("keeps an unterminated triple-quoted string as one string run", () => {
    const lines = highlightPython('x = """start\nmiddle\nend"""');
    expect(lines[1].every((tk) => tk.t === "str")).toBe(true);
  });
});
