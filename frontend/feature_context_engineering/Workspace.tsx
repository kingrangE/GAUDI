"use client";

import { useEffect, useState } from "react";

import { fetchProject, fetchProjects, submitClaudeMd } from "./api";
import { ContextPane, type SubmitStatus } from "./ContextPane";
import { FileWell, type ViewFile } from "./FileWell";
import { ProjectPane } from "./ProjectPane";
import type { EvaluationReport, Project } from "./types";
import styles from "./workspace.module.css";

interface WorkspaceProps {
  projectId: string;
  // Provided by the server on assembly; otherwise the client fetches it.
  initialProject?: Project;
  /** When true: locks to projectId, hides the picker, and routes submit through onExamSubmit. */
  examMode?: boolean;
  /** Called instead of the internal grading submit when examMode is true. */
  onExamSubmit?: (claudeMd: string) => Promise<void>;
}

/** Default file shown before the user picks one (prefer README, else the first file). */
function firstFile(project: Project): ViewFile | null {
  return (
    project.files.find((f) => f.path === "README.md") ??
    project.files.find((f) => f.kind === "file") ??
    null
  );
}

export function Workspace({ projectId, initialProject, examMode, onExamSubmit }: WorkspaceProps) {
  const [currentId, setCurrentId] = useState(projectId);
  const [project, setProject] = useState<Project | null>(initialProject ?? null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<ViewFile | null>(null);
  const [status, setStatus] = useState<SubmitStatus>("idle");
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [submitted, setSubmitted] = useState(0);
  const [loadError, setLoadError] = useState(false);

  // Load the project list for the picker (best effort). Skipped in exam mode.
  useEffect(() => {
    if (examMode) return;
    let active = true;
    fetchProjects()
      .then((list) => {
        if (active && Array.isArray(list)) {
          setProjects(list);
        }
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [examMode]);

  // Load the selected project (skip if the initial one was supplied).
  useEffect(() => {
    if (currentId === projectId && initialProject) {
      setProject(initialProject);
      return;
    }
    let active = true;
    setProject(null);
    setLoadError(false);
    fetchProject(currentId)
      .then((p) => {
        if (active) {
          setProject(p);
        }
      })
      .catch(() => {
        if (active) {
          setLoadError(true);
        }
      });
    return () => {
      active = false;
    };
  }, [currentId, projectId, initialProject]);

  function selectProject(id: string) {
    if (id === currentId) {
      return;
    }
    setCurrentId(id);
    setSelected(null);
    setStatus("idle");
    setReport(null);
  }

  async function handleSubmit(claudeMd: string) {
    if (!project) {
      return;
    }
    setStatus("submitting");
    setReport(null);
    try {
      if (examMode && onExamSubmit) {
        await onExamSubmit(claudeMd);
      } else {
        const result = await submitClaudeMd({ project_id: project.id, claude_md: claudeMd });
        setReport(result);
      }
      setStatus("done");
      setSubmitted((n) => n + 1);
    } catch {
      setStatus("error");
    }
  }

  if (!project) {
    return (
      <div className={styles.loading}>
        {loadError ? "프로젝트를 불러오지 못했습니다." : "프로젝트를 불러오는 중…"}
      </div>
    );
  }

  const shown = selected ?? firstFile(project);

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <span className={styles.brand}>and·you</span>
        <span className={styles.feature}>CONTEXT ENGINEERING</span>
        {!examMode && projects.length > 1 ? (
          <select
            className={styles.picker}
            aria-label="프로젝트 선택"
            value={currentId}
            onChange={(e) => selectProject(e.target.value)}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
        ) : null}
        <span className={styles.spacer} />
        <span className={styles.attempts}>제출 {submitted}</span>
      </header>
      <main className={styles.grid}>
        <ProjectPane
          project={project}
          selectedPath={shown?.path ?? null}
          onSelect={(node) => setSelected(node)}
        />
        <FileWell file={shown} />
        <ContextPane onSubmit={handleSubmit} status={status} report={report} examMode={examMode} />
      </main>
    </div>
  );
}
