"""Deterministic unit tests for the pure metric functions."""

import pytest

from app.harness.metrics import cohen_kappa, cv, flip_rate, mae, mean_std, pearson_r

pytestmark = pytest.mark.harness


def test_mean_std():
    m, sd = mean_std([2, 4, 4, 4, 5, 5, 7, 9])
    assert m == 5.0
    assert sd == pytest.approx(2.0)


def test_mean_std_empty():
    assert mean_std([]) == (0.0, 0.0)


def test_cv():
    assert cv([2, 4, 4, 4, 5, 5, 7, 9]) == pytest.approx(2.0 / 5.0)
    assert cv([0, 0, 0]) == 0.0  # mean 0 guard


def test_mae():
    assert mae([1, 2, 3], [1, 2, 5]) == pytest.approx(2 / 3)
    assert mae([], []) == 0.0
    with pytest.raises(ValueError):
        mae([1], [1, 2])


def test_pearson_perfect_positive_and_negative():
    assert pearson_r([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert pearson_r([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)


def test_pearson_zero_variance_returns_zero():
    assert pearson_r([1, 1, 1], [1, 2, 3]) == 0.0


def test_cohen_kappa_perfect_with_variation():
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == pytest.approx(1.0)


def test_cohen_kappa_chance_is_negative():
    assert cohen_kappa([1, 1, 0, 0], [0, 0, 1, 1]) == pytest.approx(-1.0)


def test_cohen_kappa_no_variability():
    # both raters all 1s: perfect observed agreement => 1.0
    assert cohen_kappa([1, 1, 1], [1, 1, 1]) == 1.0


def test_flip_rate():
    assert flip_rate(["a", "b", "a"], ["a", "a", "a"]) == pytest.approx(1 / 3)
    assert flip_rate(["a", "b"], ["a", "b"]) == 0.0
    assert flip_rate([], []) == 0.0
