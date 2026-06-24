"""Scorer seam. Scoring itself is a SEPARATE track (SPEC §5) — only the interface lives here.

A scorer (e.g. an LLM-as-judge over the references' rubric, or a deterministic efficiency-delta
scorer) is implemented separately and attached via `register_scorer`. This feature ships with
no scorer registered, so `evaluate` returns a placeholder result until one is added.
"""

from __future__ import annotations

from typing import Protocol

from feature_context_engineering.models import ComponentScore, Project, Submission


class ContextScorer(Protocol):
    """A pluggable scorer for a submitted CLAUDE.md."""

    name: str

    def score(self, submission: Submission, project: Project) -> ComponentScore: ...


_SCORERS: list[ContextScorer] = []


def register_scorer(scorer: ContextScorer) -> None:
    """Attach a scorer to the evaluation pipeline."""

    _SCORERS.append(scorer)


def get_scorers() -> list[ContextScorer]:
    """Return registered scorers (empty until the separate scoring track lands)."""

    return list(_SCORERS)


def clear_scorers() -> None:
    """Remove all registered scorers (used to isolate tests)."""

    _SCORERS.clear()
