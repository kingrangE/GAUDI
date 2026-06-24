"""Pure statistical primitives for the harness.

No LLM, no DB, no I/O — every function here is deterministic and unit-tested
directly. Kept dependency-free (no numpy) so the harness stays light.
"""

import math
from collections.abc import Sequence


def mean(values: Sequence[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def mean_std(values: Sequence[float]) -> tuple[float, float]:
    """Population mean and standard deviation."""
    values = list(values)
    if not values:
        return 0.0, 0.0
    m = sum(values) / len(values)
    var = sum((v - m) ** 2 for v in values) / len(values)
    return m, math.sqrt(var)


def cv(values: Sequence[float]) -> float:
    """Coefficient of variation = std / |mean| (0.0 when mean is 0)."""
    m, sd = mean_std(values)
    return sd / abs(m) if m != 0 else 0.0


def mae(a: Sequence[float], b: Sequence[float]) -> float:
    """Mean absolute error between paired sequences."""
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError("sequences must be the same length")
    if not a:
        return 0.0
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def pearson_r(a: Sequence[float], b: Sequence[float]) -> float:
    """Pearson correlation. Returns 0.0 when either side has zero variance."""
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError("sequences must be the same length")
    n = len(a)
    if n == 0:
        return 0.0
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = math.sqrt(sum((x - ma) ** 2 for x in a))
    vb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if va == 0 or vb == 0:
        return 0.0
    return cov / (va * vb)


def cohen_kappa(a: Sequence[int], b: Sequence[int]) -> float:
    """Cohen's kappa for two raters' binary (0/1) labels.

    Returns 1.0 on perfect agreement. When raters always agree *and* there is no
    label variation (e.g. all 1s), kappa is defined here as 1.0.
    """
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError("sequences must be the same length")
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    # marginal probabilities of label "1" for each rater
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if pe == 1.0:
        # no variability in expected agreement; perfect observed => 1.0 else 0.0
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)


def flip_rate(a: Sequence, b: Sequence) -> float:
    """Fraction of paired positions where the two sequences disagree.

    For position-bias: ``a`` = winning submission when shown order (X, Y),
    ``b`` = winning submission when shown order (Y, X). Disagreement => the
    verdict flipped purely from ordering.
    """
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError("sequences must be the same length")
    if not a:
        return 0.0
    return sum(1 for x, y in zip(a, b) if x != y) / len(a)
