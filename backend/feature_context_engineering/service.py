"""Orchestration: serve sample projects, capture CLAUDE.md submissions.

Scoring is a SEPARATE track (SPEC §5): `evaluate` runs whatever scorers are registered and
returns an empty-scored placeholder when none are — the feature is complete without scoring.
"""

from __future__ import annotations

from feature_context_engineering.models import EvaluationResult, Project, Submission
from feature_context_engineering.projects import get_project, list_projects
from feature_context_engineering.scorer import get_scorers

__all__ = ["create_submission", "evaluate", "get_project", "list_projects"]


def create_submission(project_id: str, claude_md: str) -> Submission:
    """Validate and build a candidate submission for a project."""

    if get_project(project_id) is None:
        raise ValueError(f"unknown project: {project_id}")
    if not claude_md.strip():
        raise ValueError("empty submission: CLAUDE.md is blank")
    return Submission(project_id=project_id, claude_md=claude_md)


def evaluate(submission: Submission, project: Project | None = None) -> EvaluationResult:
    """Run registered scorers over a submission.

    With no scorer registered (default), returns a placeholder result with empty scores; the
    scoring track attaches later via `scorer.register_scorer`.
    """

    project = project or get_project(submission.project_id)
    if project is None:
        raise ValueError(f"unknown project: {submission.project_id}")
    scores = [s.score(submission, project) for s in get_scorers()]
    total = round(sum(s.score for s in scores), 4)
    return EvaluationResult(
        project_id=submission.project_id,
        claude_md=submission.claude_md,
        scores=scores,
        total=total,
    )
