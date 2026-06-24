"""Deterministic axes: grounding + conciseness (no LLM)."""

from feature_context_engineering.models import Submission
from feature_context_engineering.projects import get_project
from feature_context_engineering.references import get_reference
from feature_context_engineering.static_checks import (
    efficiency_dimension,
    grounding_dimension,
)


def test_grounding_full_for_real_refs():
    project = get_project("board-api")
    sub = Submission(
        project_id="board-api",
        claude_md="`app/main.py` wires `app/routers/posts.py`. Test with `make test`.",
    )
    d = grounding_dimension(project, sub)
    assert d.key == "grounding"
    assert d.score == 100.0


def test_grounding_penalizes_hallucination():
    project = get_project("board-api")
    sub = Submission(
        project_id="board-api",
        claude_md="See `app/nope.py` and `src/ghost.ts`; run `make deploy`.",
    )
    assert grounding_dimension(project, sub).score < 50.0


def test_grounding_zero_when_no_refs():
    project = get_project("board-api")
    sub = Submission(project_id="board-api", claude_md="이 프로젝트는 좋은 코드를 작성합니다.")
    assert grounding_dimension(project, sub).score == 0.0


def test_grounding_on_gold_is_high():
    project = get_project("board-api")
    sub = Submission(project_id="board-api", claude_md=get_reference("board-api"))
    assert grounding_dimension(project, sub).score >= 70.0


def test_efficiency_full_for_small_token_cost_floor_for_bloat():
    short = Submission(project_id="x", claude_md="\n".join(f"line {i}" for i in range(30)))
    d = efficiency_dimension(short)
    assert d.key == "efficiency"
    assert d.score == 100.0
    assert "토큰" in d.detail

    big = "\n".join(f"행 번호 {i} 내용" for i in range(3000))
    assert efficiency_dimension(Submission(project_id="x", claude_md=big)).score == 30.0
