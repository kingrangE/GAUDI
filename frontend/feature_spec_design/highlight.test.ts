import { describe, expect, it } from "vitest";

import { highlightPython } from "./highlight";

describe("highlightPython", () => {
  it("tokenizes keywords, strings and comments on a line", () => {
    const [line] = highlightPython('def f(): return "x"  # c');
    const kinds = line.map((t) => t.t);
    expect(kinds).toContain("kw"); // def / return
    expect(kinds).toContain("str"); // "x"
    expect(kinds).toContain("com"); // # c
  });

  it("returns one token row per source line", () => {
    expect(highlightPython("a\nb\nc")).toHaveLength(3);
  });
});
