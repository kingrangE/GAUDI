import { describe, expect, it } from "vitest";

import { parseContentSegments } from "./sampleContent";

describe("parseContentSegments", () => {
  it("returns one text segment when there is no code fence", () => {
    expect(parseContentSegments("결정: FastAPI / PostgreSQL")).toEqual([
      { kind: "text", text: "결정: FastAPI / PostgreSQL" },
    ]);
  });
  it("extracts a fenced code block with its language", () => {
    expect(parseContentSegments("```python\nx = 1\nprint(x)\n```")).toEqual([
      { kind: "code", lang: "python", code: "x = 1\nprint(x)" },
    ]);
  });
  it("splits mixed prose and code in order", () => {
    expect(parseContentSegments("결정:\n- FastAPI\n\n```py\nrun()\n```\n끝")).toEqual([
      { kind: "text", text: "결정:\n- FastAPI" },
      { kind: "code", lang: "py", code: "run()" },
      { kind: "text", text: "끝" },
    ]);
  });
  it("handles a fence with no language", () => {
    expect(parseContentSegments("```\nplain\n```")).toEqual([
      { kind: "code", lang: "", code: "plain" },
    ]);
  });
  it("returns nothing for blank content", () => {
    expect(parseContentSegments("   ")).toEqual([]);
  });
});
