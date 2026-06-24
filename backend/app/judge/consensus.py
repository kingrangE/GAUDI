"""Run one judge call N times and reduce the samples to a stable verdict + a dispersion signal.

Seam-agnostic: ``judge_fn`` is any async thunk returning a single judge result, so it wraps the
structured-output judge (``app.llm``) or the raw-completion judge (``llm.client``) without caring
which. This is the live counterpart to the offline consistency harness (``app.harness``): it
attacks judge non-determinism — the failure mode a single-shot LLM judge is most prone to — by
voting over repeated samples and surfacing how much they disagreed as a confidence signal.

``tally``/``vote`` reduce categorical verdicts (e.g. "A"/"B"/"tie", covered=true/false) to a
majority + agreement fraction; ``reduce_scores``/``consensus_score`` reduce a repeated 0–100
judgement to a median (robust to one outlier run) plus a coefficient of variation that flags when
the judge is unstable for that input.
"""

from __future__ import annotations

import asyncio
import statistics
from collections import Counter
from collections.abc import Awaitable, Callable, Hashable, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from app.harness.metrics import cv as _cv
from app.harness.metrics import mean_std

T = TypeVar("T")
H = TypeVar("H", bound=Hashable)


async def sample(judge_fn: Callable[[], Awaitable[T]], n: int) -> list[T]:
    """Invoke ``judge_fn`` ``n`` times concurrently, dropping any call that raises.

    Returning only the successful samples means one malformed judge response degrades the
    consensus gracefully instead of failing the whole evaluation.
    """

    if n < 1:
        raise ValueError("n must be >= 1")
    outcomes = await asyncio.gather(*(judge_fn() for _ in range(n)), return_exceptions=True)
    return [o for o in outcomes if not isinstance(o, Exception)]


@dataclass
class Vote(Generic[H]):
    """Majority vote over categorical judge outputs."""

    winner: H
    agreement: float  # share of samples equal to the winner (1.0 = unanimous)
    counts: dict[H, int]
    n: int


def tally(values: Sequence[H]) -> Vote[H]:
    """Reduce categorical samples to the modal verdict + how strongly the judge agreed."""

    vals = list(values)
    if not vals:
        raise ValueError("no samples to tally")
    counts = Counter(vals)
    winner, top = counts.most_common(1)[0]
    return Vote(winner=winner, agreement=top / len(vals), counts=dict(counts), n=len(vals))


@dataclass
class ScoreConsensus:
    """Reduction of repeated numeric judgements + a stability signal."""

    median: float
    mean: float
    std: float
    cv: float  # std/|mean|; high => the judge is unstable for this input
    n: int


def reduce_scores(scores: Sequence[float]) -> ScoreConsensus:
    """Median (robust to one outlier run) + CV (how much the judge wobbled)."""

    vals = [float(s) for s in scores]
    if not vals:
        raise ValueError("no scores to reduce")
    m, sd = mean_std(vals)
    return ScoreConsensus(median=statistics.median(vals), mean=m, std=sd, cv=_cv(vals), n=len(vals))


async def vote(judge_fn: Callable[[], Awaitable[H]], n: int = 3) -> Vote[H]:
    """Sample a categorical judge ``n`` times and return the majority verdict."""

    return tally(await sample(judge_fn, n))


async def consensus_score(judge_fn: Callable[[], Awaitable[float]], n: int = 3) -> ScoreConsensus:
    """Sample a numeric judge ``n`` times and return the median + dispersion."""

    return reduce_scores(await sample(judge_fn, n))
