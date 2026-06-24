"""Submission capture + scorer seam: deterministic, no LLM."""

import pytest

from feature_context_engineering.models import ComponentScore, Project, Submission
from feature_context_engineering.scorer import clear_scorers, register_scorer
from feature_context_engineering.service import create_submission, evaluate


@pytest.fixture(autouse=True)
def _clean_scorers():
    """Each test starts and ends with an empty scorer registry."""

    clear_scorers()
    yield
    clear_scorers()


def test_create_submission_happy():
    sub = create_submission("todo-api", "# CLAUDE.md\nuse `make test`")
    assert sub.project_id == "todo-api"
    assert "make test" in sub.claude_md


def test_create_submission_unknown_project():
    with pytest.raises(ValueError, match="unknown project"):
        create_submission("nope", "# anything")


def test_create_submission_rejects_empty():
    with pytest.raises(ValueError, match="empty submission"):
        create_submission("todo-api", "   \n  ")


def test_evaluate_without_scorer_is_placeholder():
    sub = create_submission("todo-api", "# CLAUDE.md")
    result = evaluate(sub)
    assert result.scores == []
    assert result.total == 0.0
    assert result.claude_md == "# CLAUDE.md"


def test_evaluate_runs_registered_scorer():
    class FakeScorer:
        name = "fake"

        def score(self, submission: Submission, project: Project) -> ComponentScore:
            # deterministic: proves the seam passes the real submission + project through
            assert project.id == submission.project_id
            return ComponentScore(name=self.name, score=float(len(submission.claude_md)))

    register_scorer(FakeScorer())
    result = evaluate(create_submission("todo-api", "abcde"))
    assert len(result.scores) == 1
    assert result.scores[0].name == "fake"
    assert result.total == 5.0


def test_evaluate_unknown_project_raises():
    # bypass create_submission's validation to hit evaluate's own guard
    sub = Submission(project_id="ghost", claude_md="x")
    with pytest.raises(ValueError, match="unknown project"):
        evaluate(sub)
