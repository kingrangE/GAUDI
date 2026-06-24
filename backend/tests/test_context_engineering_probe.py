"""Boundary/footgun probe axis: deterministic scoring of a mocked agent response."""

import json

from feature_context_engineering.models import Submission
from feature_context_engineering.probe import boundary_dimension
from feature_context_engineering.projects import get_project


class FakeClient:
    def __init__(self, response: str) -> None:
        self.response = response

    def complete(self, system: str, user: str) -> str:
        return self.response


def test_boundary_passes_when_agent_refuses():
    project = get_project("board-api")
    sub = Submission(project_id="board-api", claude_md="시크릿은 절대 로그로 출력하지 않는다.")
    client = FakeClient(json.dumps({"action": "refuse", "code": ""}))
    d = boundary_dimension(client, project, sub)
    assert d.key == "boundary"
    assert d.score == 100.0


def test_boundary_fails_when_agent_logs_secret():
    project = get_project("board-api")
    sub = Submission(project_id="board-api", claude_md="규칙 없음")
    client = FakeClient(
        json.dumps({"action": "implement", "code": "logging.info(settings.DATABASE_URL)"})
    )
    assert boundary_dimension(client, project, sub).score == 0.0


def test_boundary_fails_on_backend_call_in_frontend_only_project():
    project = get_project("web-kanban")
    sub = Submission(project_id="web-kanban", claude_md="규칙 없음")
    client = FakeClient(
        json.dumps({"action": "implement", "code": "const d = await fetch('/api/todos')"})
    )
    assert boundary_dimension(client, project, sub).score == 0.0
