"""FastAPI surface for the context-engineering feature. Wired into the app at assembly."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from feature_context_engineering.evaluate import build_report
from feature_context_engineering.models import EvaluationReport, Project, Submission
from feature_context_engineering.service import create_submission, get_project, list_projects
from llm.client import get_llm_client
from llm.config import get_settings

router = APIRouter(prefix="/api/context-engineering", tags=["context-engineering"])


@router.get("/projects", response_model=list[Project])
def get_projects() -> list[Project]:
    return list_projects()


@router.get("/projects/{project_id}", response_model=Project)
def get_one_project(project_id: str) -> Project:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"unknown project: {project_id}")
    return project


@router.post("/submissions", response_model=EvaluationReport)
def post_submission(submission: Submission) -> EvaluationReport:
    try:
        captured = create_submission(submission.project_id, submission.claude_md)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    project = get_project(captured.project_id)
    assert project is not None  # create_submission already validated existence

    # Deterministic axes always run; coverage/boundary run only when an LLM is configured.
    settings = get_settings()
    client = get_llm_client(settings) if settings.api_key else None
    return build_report(project, captured, client)
