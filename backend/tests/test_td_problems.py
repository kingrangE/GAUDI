"""Validate the version-controlled problem fixtures."""

from app.features.test_design.problems import (
    PROBLEM_COUNT,
    PROBLEMS,
    find_problem,
    get_problem,
)

_SEVERITIES = {"low", "medium", "high"}
_CATEGORIES = {"correctness", "edge_case", "validation", "security", "performance"}


def test_there_are_five_problems():
    assert PROBLEM_COUNT == 5
    assert len(PROBLEMS) == 5


def test_problem_ids_unique():
    ids = [p.id for p in PROBLEMS]
    assert len(set(ids)) == len(ids)


def test_each_problem_well_formed():
    for p in PROBLEMS:
        assert p.title and p.spec and p.code.strip()
        assert p.flaws, f"{p.id} has no ground-truth flaws"
        flaw_ids = [f.id for f in p.flaws]
        assert len(set(flaw_ids)) == len(flaw_ids), f"{p.id} has duplicate flaw ids"
        for f in p.flaws:
            assert f.text.strip()
            assert f.severity in _SEVERITIES
            assert f.category in _CATEGORIES


def test_lookup_helpers():
    assert get_problem(0) is PROBLEMS[0]
    assert find_problem(PROBLEMS[2].id) is PROBLEMS[2]
    assert find_problem("does_not_exist") is None
