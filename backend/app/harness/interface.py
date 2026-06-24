"""The JudgeAdapter contract that decouples the harness from any one feature.

The harness analyses (consistency / agreement / position-bias / self-preference)
depend only on this interface, so any feature can be plugged in by implementing
an adapter. test_design provides the first one in
``app.features.test_design.harness_adapter``.
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ScoreOutcome:
    """The judge's outcome for one (problem, candidate flaws) pair."""

    gt_ids: list[str]  # all ground-truth flaw ids for the problem
    matched_ids: list[str] = field(default_factory=list)  # gt flaws the candidate found
    recall: float = 0.0
    precision: float = 0.0
    weighted_score: float = 0.0
    mean_quality: float = 0.0


class JudgeAdapter(Protocol):
    name: str

    async def score(self, problem_index: int, flaws: list[str]) -> ScoreOutcome:
        """Judge one submission and return its scored outcome."""
        ...

    async def pairwise(
        self, problem_index: int, flaws_a: list[str], flaws_b: list[str]
    ) -> str:
        """Return which submission is stronger: 'A', 'B', or 'tie'."""
        ...
