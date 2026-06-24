import { describe, expect, it } from "vitest";

import { buildTree } from "./tree";
import type { FileNode } from "./types";

const FILES: FileNode[] = [
  { path: "README.md", kind: "file", content: "# readme" },
  { path: "app", kind: "dir", content: null },
  { path: "app/main.py", kind: "file", content: "print('hi')" },
  { path: "app/routes", kind: "dir", content: null },
  { path: "app/routes/todos.py", kind: "file", content: "router = ..." },
];

describe("buildTree", () => {
  it("nests files under their directory nodes", () => {
    const roots = buildTree(FILES);
    expect(roots.map((n) => n.path).sort()).toEqual(["README.md", "app"]);

    const app = roots.find((n) => n.path === "app");
    expect(app?.kind).toBe("dir");
    expect(app?.children.map((c) => c.path).sort()).toEqual(["app/main.py", "app/routes"]);

    const routes = app?.children.find((c) => c.path === "app/routes");
    expect(routes?.children.map((c) => c.path)).toEqual(["app/routes/todos.py"]);
  });

  it("uses the basename as the node name and keeps file content", () => {
    const readme = buildTree(FILES).find((n) => n.path === "README.md");
    expect(readme?.name).toBe("README.md");
    expect(readme?.content).toBe("# readme");
  });

  it("is order-independent (sorts internally so parents resolve)", () => {
    const shuffled = [FILES[2], FILES[4], FILES[0], FILES[3], FILES[1]];
    expect(buildTree(shuffled).map((n) => n.path).sort()).toEqual(["README.md", "app"]);
  });

  it("returns an empty array for no files", () => {
    expect(buildTree([])).toEqual([]);
  });
});
