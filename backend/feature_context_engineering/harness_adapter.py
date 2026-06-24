"""context-engineering's implementation of the harness ``JudgeAdapter``.

Maps the CLAUDE.md coverage judge onto the reliability harness so the consistency / agreement /
position-bias / self-preference analyses run against it. ``score`` runs the per-criterion coverage
judge and reports it as a ``ScoreOutcome`` (rubric criteria = ground-truth ids, covered = matched);
``pairwise`` runs the A/B doc comparison. The judge client mirrors the *live* judge's temperature
(optionally model-pinned) so the consistency analysis reflects the real single-judge noise the live
coverage consensus absorbs, and self-preference can vary the judge model.

The harness interface speaks in ``(problem_index, flaws)``; here ``problem_index`` selects a project
and ``flaws[0]`` carries the candidate CLAUDE.md text.
"""

from __future__ import annotations

import asyncio

from app.harness.interface import ScoreOutcome
from feature_context_engineering.judge import coverage_score, judge_pairwise, judge_submission
from feature_context_engineering.models import Submission
from feature_context_engineering.projects import list_projects
from feature_context_engineering.rubric import get_rubric
from llm.client import OpenAIClient
from llm.config import LLMSettings, get_settings


def _judge_client(model: str | None) -> OpenAIClient:
    """A judge client mirroring the live judge's temperature, optionally pinned to a model.

    Reliability is measured at the *production* temperature so the consistency analysis surfaces
    the real single-judge noise (which the live coverage consensus absorbs).
    """

    base = get_settings()
    return OpenAIClient(
        LLMSettings(
            provider=base.provider,
            model=model or base.model,
            temperature=base.temperature,
            api_key=base.api_key,
            max_tokens=base.max_tokens,
        )
    )


class ContextEngAdapter:
    """Drives context-engineering's coverage + pairwise judges behind the harness interface."""

    name = "context_engineering"

    def __init__(self, model: str | None = None) -> None:
        self.model = model
        self._client = _judge_client(model)
        self._projects = list_projects()

    def _project(self, problem_index: int):
        return self._projects[problem_index]

    async def score(self, problem_index: int, flaws: list[str]) -> ScoreOutcome:
        project = self._project(problem_index)
        criteria = get_rubric(project.id)
        submission = Submission(project_id=project.id, claude_md=flaws[0] if flaws else "")
        verdicts = await asyncio.to_thread(
            judge_submission, self._client, project, submission, criteria
        )
        covered = [v.id for v in verdicts if v.covered]
        total = len(criteria) or 1
        return ScoreOutcome(
            gt_ids=[c.id for c in criteria],
            matched_ids=covered,
            recall=round(len(covered) / total, 4),
            weighted_score=round(coverage_score(verdicts, criteria) / 100, 4),
        )

    async def pairwise(self, problem_index: int, flaws_a: list[str], flaws_b: list[str]) -> str:
        project = self._project(problem_index)
        sub_a = Submission(project_id=project.id, claude_md=flaws_a[0] if flaws_a else "")
        sub_b = Submission(project_id=project.id, claude_md=flaws_b[0] if flaws_b else "")
        return await asyncio.to_thread(judge_pairwise, self._client, project, sub_a, sub_b)
