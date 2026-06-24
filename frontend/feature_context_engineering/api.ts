// HTTP client for the context-engineering backend. The client never calls an LLM directly.

import type { EvaluationReport, Project, Submission } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const PREFIX = "/api/context-engineering";

async function readJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(`요청 실패 (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}${PREFIX}/projects`);
  return readJson<Project[]>(res);
}

export async function fetchProject(projectId: string): Promise<Project> {
  const res = await fetch(`${API_BASE}${PREFIX}/projects/${encodeURIComponent(projectId)}`);
  return readJson<Project>(res);
}

export async function submitClaudeMd(submission: Submission): Promise<EvaluationReport> {
  const res = await fetch(`${API_BASE}${PREFIX}/submissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(submission),
  });
  return readJson<EvaluationReport>(res);
}
