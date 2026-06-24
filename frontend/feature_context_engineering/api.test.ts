import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchProject, fetchProjects, submitClaudeMd } from "./api";
import type { EvaluationReport, Project } from "./types";

const PROJECT: Project = { id: "todo-api", title: "todo-api", brief: "b", files: [] };

function jsonRes(data: unknown, ok = true, status = 200): Response {
  return { ok, status, json: async () => data } as unknown as Response;
}

afterEach(() => vi.unstubAllGlobals());

describe("context-engineering api", () => {
  it("lists projects from the projects endpoint", async () => {
    const f = vi.fn(async () => jsonRes([PROJECT]));
    vi.stubGlobal("fetch", f);

    expect(await fetchProjects()).toEqual([PROJECT]);
    expect(String((f.mock.calls[0] as unknown[])[0])).toContain(
      "/api/context-engineering/projects",
    );
  });

  it("fetches a single project by id (encoded)", async () => {
    const f = vi.fn(async () => jsonRes(PROJECT));
    vi.stubGlobal("fetch", f);

    await fetchProject("todo api");
    expect(String((f.mock.calls[0] as unknown[])[0])).toContain(
      "/api/context-engineering/projects/todo%20api",
    );
  });

  it("posts a submission as JSON", async () => {
    const result: EvaluationReport = {
      project_id: "todo-api",
      scored: true,
      total: 80,
      dimensions: [],
      results: [],
    };
    const f = vi.fn(async () => jsonRes(result));
    vi.stubGlobal("fetch", f);

    const out = await submitClaudeMd({ project_id: "todo-api", claude_md: "# c" });
    expect(out).toEqual(result);

    const call = f.mock.calls[0] as unknown[];
    expect(String(call[0])).toContain("/api/context-engineering/submissions");
    const init = call[1] as RequestInit;
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({ project_id: "todo-api", claude_md: "# c" });
  });

  it("throws on a non-ok response", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonRes(null, false, 500)));
    await expect(fetchProjects()).rejects.toThrow("요청 실패 (500)");
  });
});
