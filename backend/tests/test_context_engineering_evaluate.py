"""Composite scorer: four axes combined, with and without an LLM client."""

import json

from feature_context_engineering.evaluate import build_report
from feature_context_engineering.models import Submission
from feature_context_engineering.projects import get_project
from feature_context_engineering.references import get_reference
from feature_context_engineering.rubric import get_rubric


class FakeClient:
    """Routes by prompt: boundary probe prompts contain '작업 요청', coverage ones don't."""

    def __init__(self, coverage_raw: str, boundary_raw: str) -> None:
        self.coverage_raw = coverage_raw
        self.boundary_raw = boundary_raw

    def complete(self, system: str, user: str) -> str:
        return self.boundary_raw if "작업 요청" in user else self.coverage_raw


def test_without_client_runs_deterministic_axes_only():
    project = get_project("board-api")
    sub = Submission(project_id="board-api", claude_md=get_reference("board-api"))

    report = build_report(project, sub, client=None)
    dims = {d.key: d for d in report.dimensions}

    assert report.scored is True
    assert dims["coverage"].available is False
    assert dims["boundary"].available is False
    assert dims["grounding"].available is True
    assert dims["efficiency"].available is True
    assert report.total > 0  # grounding + conciseness still produce a composite
    assert report.results == []


def test_with_client_composes_four_axes():
    project = get_project("board-api")
    ids = [c.id for c in get_rubric("board-api")]
    marker = "EV"
    sub = Submission(
        project_id="board-api",
        claude_md=f"`app/main.py` and `make test` cover it {marker}",
    )
    coverage_raw = json.dumps([{"id": i, "covered": True, "evidence": marker} for i in ids])
    boundary_raw = json.dumps({"action": "refuse", "code": ""})

    report = build_report(project, sub, FakeClient(coverage_raw, boundary_raw))
    dims = {d.key: d for d in report.dimensions}

    assert all(dims[k].available for k in ("coverage", "grounding", "boundary", "efficiency"))
    assert dims["coverage"].score == 100.0
    assert dims["boundary"].score == 100.0
    assert report.results and {r.id for r in report.results} == set(ids)
    assert 0 < report.total <= 100
