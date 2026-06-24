"""Validate the version-controlled problem fixtures."""

from app.features.test_design.problems import (
    PROBLEM_COUNT,
    PROBLEMS,
    find_problem,
    get_problem,
)

_SEVERITIES = {"low", "medium", "high"}
_DIFFICULTIES = {"easy", "medium", "hard"}
_CATEGORIES = {
    "boundary",
    "error_handling",
    "concurrency",
    "security",
    "data_integrity",
    "validation",
    "performance",
    "correctness",
}


def test_there_are_six_problems():
    assert PROBLEM_COUNT == 6
    assert len(PROBLEMS) == 6


def test_problem_ids_unique():
    ids = [p.id for p in PROBLEMS]
    assert len(set(ids)) == len(ids)


def test_two_problems_per_difficulty_tier():
    counts = {d: sum(1 for p in PROBLEMS if p.difficulty == d) for d in _DIFFICULTIES}
    assert counts == {"easy": 2, "medium": 2, "hard": 2}


def test_each_problem_well_formed():
    for p in PROBLEMS:
        assert p.title and p.spec.strip()
        assert p.difficulty in _DIFFICULTIES
        assert p.provided_tests, f"{p.id} has no provided basic tests"
        assert all(t.strip() for t in p.provided_tests)
        assert p.flaws, f"{p.id} has no ground-truth verification items"
        flaw_ids = [f.id for f in p.flaws]
        assert len(set(flaw_ids)) == len(flaw_ids), f"{p.id} has duplicate item ids"
        for f in p.flaws:
            assert f.text.strip()
            assert f.severity in _SEVERITIES
            assert f.category in _CATEGORIES


def test_lookup_helpers():
    assert get_problem(0) is PROBLEMS[0]
    assert find_problem(PROBLEMS[2].id) is PROBLEMS[2]
    assert find_problem("does_not_exist") is None
