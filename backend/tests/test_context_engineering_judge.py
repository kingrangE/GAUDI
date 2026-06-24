"""LLM-as-judge coverage scoring: deterministic via a mocked LLM client (no network)."""

import json

from feature_context_engineering.judge import (
    ChecklistJudgeScorer,
    coverage_score,
    judge_submission,
    parse_verdicts,
)
from feature_context_engineering.models import Criterion, Submission
from feature_context_engineering.projects import get_project, list_projects
from feature_context_engineering.rubric import get_rubric


class FakeClient:
    """Records calls and returns a canned judge response."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.response


CRITERIA = [
    Criterion(id="a", text="A", weight=1.0),
    Criterion(id="b", text="B", weight=2.0),
    Criterion(id="c", text="C", weight=1.0),
]
SUB = Submission(project_id="x", claude_md="line about A here\nand B detail\n")


def test_every_project_has_a_rubric_with_unique_ids():
    for project in list_projects():
        crits = get_rubric(project.id)
        assert crits, project.id
        ids = [c.id for c in crits]
        assert len(ids) == len(set(ids)), project.id


def test_parse_grounds_evidence_and_marks_missing():
    raw = json.dumps(
        [
            {"id": "a", "covered": True, "evidence": "A here"},
            {"id": "b", "covered": True, "evidence": "not in the document"},  # hallucinated
            # "c" omitted entirely
        ]
    )
    by = {v.id: v for v in parse_verdicts(raw, CRITERIA, SUB)}
    assert by["a"].covered is True
    assert by["b"].covered is False  # evidence not in submission -> downgraded
    assert by["c"].covered is False  # missing from output -> not covered


def test_coverage_score_is_weighted():
    raw = json.dumps(
        [
            {"id": "a", "covered": True, "evidence": "A here"},
            {"id": "b", "covered": True, "evidence": "B detail"},
            {"id": "c", "covered": False, "evidence": ""},
        ]
    )
    verdicts = parse_verdicts(raw, CRITERIA, SUB)
    # a(1) + b(2) covered of total 4 -> 75.0
    assert coverage_score(verdicts, CRITERIA) == 75.0


def test_malformed_output_scores_zero():
    verdicts = parse_verdicts("the model rambled, no json", CRITERIA, SUB)
    assert all(not v.covered for v in verdicts)
    assert coverage_score(verdicts, CRITERIA) == 0.0


def test_extracts_json_from_fenced_prose():
    raw = 'sure:\n```json\n[{"id":"a","covered":true,"evidence":"A here"}]\n```'
    by = {v.id: v.covered for v in parse_verdicts(raw, CRITERIA, SUB)}
    assert by["a"] is True


def test_judge_submission_calls_client_and_covers_rubric():
    project = get_project("board-api")
    ids = [c.id for c in get_rubric("board-api")]
    marker = "MARKER-EVIDENCE"
    sub = Submission(project_id="board-api", claude_md=f"# doc\n{marker}\n")
    client = FakeClient(json.dumps([{"id": i, "covered": True, "evidence": marker} for i in ids]))

    verdicts = judge_submission(client, project, sub)

    assert client.calls  # the LLM seam was actually invoked
    assert len(verdicts) == len(ids)
    assert all(v.covered for v in verdicts)


def test_scorer_full_coverage_is_100():
    project = get_project("board-api")
    ids = [c.id for c in get_rubric("board-api")]
    marker = "EVID"
    sub = Submission(project_id="board-api", claude_md=f"covers everything {marker}")
    raw = json.dumps([{"id": i, "covered": True, "evidence": marker} for i in ids])

    score = ChecklistJudgeScorer(FakeClient(raw)).score(sub, project)

    assert score.name == "context-coverage"
    assert score.score == 100.0
    assert "covered" in score.detail


def test_scorer_rejects_fabricated_coverage():
    # Judge claims everything is covered, but the quotes aren't in the doc -> grounding kills it.
    project = get_project("board-api")
    ids = [c.id for c in get_rubric("board-api")]
    sub = Submission(project_id="board-api", claude_md="# empty-ish doc")
    raw = json.dumps([{"id": i, "covered": True, "evidence": "fabricated quote"} for i in ids])

    score = ChecklistJudgeScorer(FakeClient(raw)).score(sub, project)

    assert score.score == 0.0
