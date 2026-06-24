"""Deterministic coherence checks for the judge-reliability harness fixtures.

These run with no LLM and no key. They guarantee the committed fixtures
(synthetic submissions + human gold + model panel) stay consistent with the
current practical-scenario problem set, so the harness always evaluates the
*live* judge against valid gold. If a problem's flaws change, these fail loudly.
"""

import json
from pathlib import Path

import pytest

from app.features.test_design.problems import PROBLEM_COUNT, PROBLEMS

pytestmark = pytest.mark.harness

_FIXTURES = Path(__file__).resolve().parents[1] / "app" / "features" / "test_design" / "fixtures"


def _load(name: str):
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


SYNTHETIC = _load("synthetic_submissions.json")
GOLD = {g["key"]: g for g in _load("human_gold.json")}
PANEL = _load("panel_models.json")


def test_synthetic_and_gold_keys_are_one_to_one():
    syn_keys = {s["key"] for s in SYNTHETIC}
    gold_keys = set(GOLD)
    assert len(syn_keys) == len(SYNTHETIC), "duplicate keys in synthetic submissions"
    assert syn_keys == gold_keys, "every synthetic submission needs exactly one gold label"


@pytest.mark.parametrize("sub", SYNTHETIC, ids=lambda s: s["key"])
def test_problem_index_in_range(sub):
    assert 0 <= sub["problem_index"] < PROBLEM_COUNT


@pytest.mark.parametrize("sub", SYNTHETIC, ids=lambda s: s["key"])
def test_author_model_is_in_panel(sub):
    assert sub["author_model"] in PANEL["author_models"]


@pytest.mark.parametrize("sub", SYNTHETIC, ids=lambda s: s["key"])
def test_submission_has_flaws(sub):
    assert sub["flaws"], "a submission must list at least one verification item"


@pytest.mark.parametrize("sub", SYNTHETIC, ids=lambda s: s["key"])
def test_gold_matched_ids_are_real_flaws_and_recall_is_consistent(sub):
    gold = GOLD[sub["key"]]
    problem = PROBLEMS[sub["problem_index"]]
    real_ids = {f.id for f in problem.flaws}

    matched = gold["matched_ids"]
    assert len(matched) == len(set(matched)), f"{sub['key']}: duplicate matched_ids"
    assert set(matched) <= real_ids, (
        f"{sub['key']}: matched_ids {matched} not all in {problem.id} flaws {sorted(real_ids)}"
    )

    expected_recall = len(matched) / len(problem.flaws)
    assert gold["recall"] == pytest.approx(expected_recall, abs=1e-3), (
        f"{sub['key']}: recall {gold['recall']} != matched/total {expected_recall:.4f}"
    )


def test_panel_judge_and_author_models_are_consistent():
    # The default adapter judges with settings.llm_model; self-preference needs
    # the author panel to overlap the judges so 'own vs others' is well-defined.
    assert PANEL["judge_models"], "need at least one judge model to sweep"
    assert PANEL["author_models"], "need at least one author model"
    authors_used = {s["author_model"] for s in SYNTHETIC}
    assert authors_used <= set(PANEL["author_models"])
    # at least two distinct authors so self-preference 'others' group is non-empty
    assert len(authors_used) >= 2
