"""cx-churn-radar 프로젝트 + 15 criteria 등록 검증. LLM 목킹, DB 불필요."""

from __future__ import annotations

import json

from feature_context_engineering.evaluate import build_report
from feature_context_engineering.models import Submission
from feature_context_engineering.projects import get_project, list_projects
from feature_context_engineering.rubric import get_rubric

VALID_CATEGORIES = {"commands", "structure", "conventions", "boundaries"}
PROJECT_ID = "cx-churn-radar"


# ── 프로젝트 등록 ─────────────────────────────────────────────────────────────


def test_cx_churn_radar_in_project_list():
    ids = [p.id for p in list_projects()]
    assert PROJECT_ID in ids


def test_cx_churn_radar_loads_with_required_fields():
    project = get_project(PROJECT_ID)
    assert project is not None
    assert project.id == PROJECT_ID
    assert project.title
    assert project.brief


def test_cx_churn_radar_file_tree_covers_key_modules():
    project = get_project(PROJECT_ID)
    assert project is not None
    paths = {f.path for f in project.files}
    for expected in [
        "app/pii.py",
        "app/pipeline/ingest.py",
        "app/pipeline/preprocess.py",
        "app/scoring/model.py",
        "app/scoring/scorer.py",
        "dags/churn_score_daily_dag.py",
        "tests/conftest.py",
    ]:
        assert expected in paths, f"missing file: {expected}"


def test_file_nodes_have_content_and_dirs_inferred():
    project = get_project(PROJECT_ID)
    assert project is not None
    files = [f for f in project.files if f.kind == "file"]
    dirs = [f for f in project.files if f.kind == "dir"]
    assert files and all(f.content for f in files), "files must carry content"
    assert all(d.content is None for d in dirs), "dir nodes must have no content"


def test_no_duplicate_paths():
    project = get_project(PROJECT_ID)
    assert project is not None
    paths = [f.path for f in project.files]
    assert len(paths) == len(set(paths)), "duplicate paths found"


def test_every_nested_file_has_parent_dir_node():
    project = get_project(PROJECT_ID)
    assert project is not None
    dir_paths = {f.path for f in project.files if f.kind == "dir"}
    for f in project.files:
        if f.kind == "file" and "/" in f.path:
            parent = f.path.rsplit("/", 1)[0]
            assert parent in dir_paths, f"parent dir missing for {f.path}"


# ── rubric ────────────────────────────────────────────────────────────────────


def test_rubric_has_exactly_15_criteria():
    criteria = get_rubric(PROJECT_ID)
    assert len(criteria) == 15, f"expected 15, got {len(criteria)}"


def test_rubric_ids_are_unique():
    criteria = get_rubric(PROJECT_ID)
    ids = [c.id for c in criteria]
    assert len(ids) == len(set(ids)), "duplicate criterion ids"


def test_rubric_categories_all_valid():
    criteria = get_rubric(PROJECT_ID)
    for c in criteria:
        assert c.category in VALID_CATEGORIES, (
            f"{c.id}: invalid category {c.category!r}"
        )


def test_rubric_weights_positive():
    criteria = get_rubric(PROJECT_ID)
    for c in criteria:
        assert c.weight > 0, f"{c.id}: weight must be positive"


def test_rubric_texts_nonempty():
    criteria = get_rubric(PROJECT_ID)
    for c in criteria:
        assert c.text.strip(), f"{c.id}: empty text"


def test_rubric_category_spread():
    """Each of the four categories must be represented."""
    criteria = get_rubric(PROJECT_ID)
    by_cat: dict[str, int] = {}
    for c in criteria:
        by_cat[c.category] = by_cat.get(c.category, 0) + 1
    for cat in VALID_CATEGORIES:
        assert by_cat.get(cat, 0) >= 1, f"category {cat!r} has no criteria"


def test_rubric_high_weight_criteria_exist():
    """PII-masking and in-memory-test criteria must carry weight >= 2.0."""
    criteria = get_rubric(PROJECT_ID)
    by_id = {c.id: c for c in criteria}
    assert by_id["conv-pii-mask"].weight >= 2.0
    assert by_id["conv-inmem-test"].weight >= 2.0
    assert by_id["bound-no-leakage"].weight >= 2.0
    assert by_id["bound-no-plain-pii"].weight >= 2.0


# ── mocked-judge EvaluationReport ─────────────────────────────────────────────


class _FakeClient:
    """Routes by prompt content: boundary prompts contain '작업 요청'."""

    def __init__(self, coverage_raw: str, boundary_raw: str) -> None:
        self.coverage_raw = coverage_raw
        self.boundary_raw = boundary_raw

    def complete(self, system: str, user: str) -> str:  # noqa: ARG002
        return self.boundary_raw if "작업 요청" in user else self.coverage_raw


def test_mocked_judge_report_total_in_range():
    project = get_project(PROJECT_ID)
    assert project is not None
    criteria = get_rubric(PROJECT_ID)
    ids = [c.id for c in criteria]
    marker = "EV"
    sub = Submission(
        project_id=PROJECT_ID,
        claude_md=(
            f"`app/pii.py`와 `pytest -q`와 `ruff check .` {marker} "
            "`app/pipeline/ingest.py` `app/scoring/model.py`"
        ),
    )
    coverage_raw = json.dumps(
        [{"id": i, "covered": True, "evidence": marker} for i in ids]
    )
    boundary_raw = json.dumps({"action": "refuse", "code": ""})

    report = build_report(project, sub, _FakeClient(coverage_raw, boundary_raw))

    assert report.scored is True
    assert 0 <= report.total <= 100
    assert {r.id for r in report.results} == set(ids)


def test_mocked_judge_all_covered_gives_full_coverage_score():
    project = get_project(PROJECT_ID)
    assert project is not None
    criteria = get_rubric(PROJECT_ID)
    ids = [c.id for c in criteria]
    marker = "EV"
    sub = Submission(
        project_id=PROJECT_ID,
        claude_md=f"full-coverage doc {marker}",
    )
    coverage_raw = json.dumps(
        [{"id": i, "covered": True, "evidence": marker} for i in ids]
    )
    boundary_raw = json.dumps({"action": "refuse", "code": ""})

    report = build_report(project, sub, _FakeClient(coverage_raw, boundary_raw))

    dims = {d.key: d for d in report.dimensions}
    assert dims["coverage"].score == 100.0


def test_without_client_deterministic_axes_only():
    project = get_project(PROJECT_ID)
    assert project is not None
    sub = Submission(
        project_id=PROJECT_ID,
        claude_md="`pytest -q` and `ruff check .` are the main commands",
    )
    report = build_report(project, sub, client=None)

    assert report.scored is True
    dims = {d.key: d for d in report.dimensions}
    assert dims["coverage"].available is False
    assert dims["boundary"].available is False
    assert dims["grounding"].available is True
    assert dims["efficiency"].available is True
    assert report.total > 0
    assert report.results == []
