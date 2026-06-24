"""Dataset + ground-truth sanity checks (no DB, no LLM).

Guards the determinism coupling: ground truth is derived from criteria_fn over
the seeded data, so it must stay non-trivial and reference only real ids.
"""

from app.features.office_prompting import datasets
from app.features.office_prompting.problems import PROBLEM_COUNT, PROBLEMS


def test_datasets_meet_floors():
    assert len(datasets.CUSTOMERS) >= 200
    assert len(datasets.ORDERS) >= 200
    assert len(datasets.PRODUCTS) >= 200
    for name, cols in datasets.COLUMNS.items():
        assert len(cols) >= 5, name


def test_generation_is_deterministic():
    again = datasets._build()
    assert again["customers"] == datasets.CUSTOMERS
    assert again["orders"] == datasets.ORDERS
    assert again["products"] == datasets.PRODUCTS


def test_three_problems():
    assert PROBLEM_COUNT == 3
    assert [p.index for p in PROBLEMS] == [0, 1, 2]


def test_ground_truth_is_non_trivial_and_valid():
    valid_customers = datasets.existing_ids("customers")
    for p in PROBLEMS:
        truth = p.ground_truth_ids
        total = len(datasets.DATASETS[p.target_table])
        assert 0 < len(truth) < total, f"{p.title}: truth size {len(truth)}"
        assert truth <= valid_customers, f"{p.title}: truth has unknown ids"


def test_ground_truth_recompute_is_stable():
    for p in PROBLEMS:
        assert p.criteria_fn() == set(p.ground_truth_ids)


def test_problems_differ():
    # The three problems should not collapse to the same answer set.
    sets = [frozenset(p.ground_truth_ids) for p in PROBLEMS]
    assert len(set(sets)) == 3
