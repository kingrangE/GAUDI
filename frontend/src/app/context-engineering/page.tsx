import { Workspace } from "../../../feature_context_engineering";
import type { Project } from "../../../feature_context_engineering";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const PROJECT_ID = "todo-api";

// Server-side fetch so the page SSRs the real registry (single source of truth = backend).
// If the backend is down, fall back to a client fetch inside the Workspace.
async function loadProject(id: string): Promise<Project | undefined> {
  try {
    const res = await fetch(`${API_BASE}/api/context-engineering/projects/${id}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return undefined;
    }
    return (await res.json()) as Project;
  } catch {
    return undefined;
  }
}

export default async function Page() {
  const project = await loadProject(PROJECT_ID);
  return <Workspace projectId={PROJECT_ID} initialProject={project} />;
}
