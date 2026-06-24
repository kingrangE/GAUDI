"""Shared judge-robustness kernel: utilities every LLM-as-judge call site can reuse.

Currently the live consensus wrapper (repeat a judge call, vote/median, report dispersion).
Cold-temperature defaults live in the LLM seams (``settings.judge_temperature``); offline
reliability measurement (consistency / agreement / bias) lives in ``app.harness``.
"""

from app.judge.consensus import (
    ScoreConsensus,
    Vote,
    consensus_score,
    reduce_scores,
    sample,
    tally,
    vote,
)

__all__ = [
    "ScoreConsensus",
    "Vote",
    "consensus_score",
    "reduce_scores",
    "sample",
    "tally",
    "vote",
]
