import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Workspace } from "./Workspace";
import type { EvaluationReport, Project } from "./types";

const project: Project = {
  id: "todo-api",
  title: "todo-api (FastAPI)",
  brief: "작은 todo API",
  files: [
    { path: "README.md", kind: "file", content: "# todo-api" },
    { path: "app", kind: "dir", content: null },
    { path: "app/main.py", kind: "file", content: "from fastapi import FastAPI\napp = FastAPI()" },
  ],
};

const evalReport: EvaluationReport = {
  project_id: "todo-api",
  scored: true,
  total: 82,
  dimensions: [
    {
      key: "coverage",
      label: "컨벤션·모호성 커버리지",
      score: 100,
      weight: 0.4,
      available: true,
      detail: "1/1 충족",
    },
    {
      key: "grounding",
      label: "정확성(grounding)",
      score: 100,
      weight: 0.25,
      available: true,
      detail: "refs 1/1 실재",
    },
  ],
  results: [
    {
      id: "cmd-test",
      text: "run the tests with make test",
      category: "commands",
      covered: true,
      evidence: "make test",
    },
  ],
};

function jsonRes(data: unknown): Response {
  return { ok: true, json: async () => data } as unknown as Response;
}

function stubFetch(list: Project[]) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: unknown) => {
      const u = String(url);
      if (u.endsWith("/submissions")) return jsonRes(evalReport);
      if (u.endsWith("/projects")) return jsonRes(list);
      return jsonRes(project);
    }),
  );
}

describe("Workspace (context-engineering)", () => {
  beforeEach(() => stubFetch([project]));
  afterEach(() => vi.unstubAllGlobals());

  it("renders the project brief and file tree", () => {
    render(<Workspace projectId="todo-api" initialProject={project} />);
    expect(screen.getByText("todo-api (FastAPI)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "main.py" })).toBeInTheDocument();
  });

  it("shows a file's content in the well when its tree node is clicked", async () => {
    const user = userEvent.setup();
    render(<Workspace projectId="todo-api" initialProject={project} />);

    await user.click(screen.getByRole("button", { name: "main.py" }));

    const well = screen.getByRole("region", { name: "파일 내용" });
    expect(well.textContent).toContain("from fastapi import FastAPI");
  });

  it("disables submit until the editor has content, then shows the score report", async () => {
    const user = userEvent.setup();
    render(<Workspace projectId="todo-api" initialProject={project} />);

    expect(screen.getByRole("button", { name: "제출" })).toBeDisabled();

    await user.type(screen.getByRole("textbox"), "# CLAUDE.md\nrun `make test`");
    await user.click(screen.getByRole("button", { name: "제출" }));

    expect(await screen.findByText("82")).toBeInTheDocument(); // composite total
    expect(screen.getByText("컨벤션·모호성 커버리지")).toBeInTheDocument(); // a dimension row
    expect(screen.getByText("run the tests with make test")).toBeInTheDocument();
  });

  it("shows a project picker when multiple projects are available", async () => {
    stubFetch([project, { ...project, id: "blog", title: "blog-api" }]);
    render(<Workspace projectId="todo-api" initialProject={project} />);

    const picker = await screen.findByRole("combobox", { name: "프로젝트 선택" });
    expect(within(picker).getByRole("option", { name: "blog-api" })).toBeInTheDocument();
  });
});
