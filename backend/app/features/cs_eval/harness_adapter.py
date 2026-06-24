"""cs_eval's implementation of the harness `JudgeAdapter`.

Wraps the live LLM judge (`judge.judge_answer`) behind the shared harness
interface so the reliability analyses can run against this feature, mirroring
``app.features.test_design.harness_adapter``. Questions are read straight from
the in-module ``QUESTIONS`` seeds (no DB), like test_design's ``get_problem``.

The cs_eval-native analyses in ``harness_eval`` use the richer ``judge`` method
(it returns the response *type*, this feature's signature). ``score`` exists only
to satisfy the ``JudgeAdapter`` Protocol — it projects the judgement onto the
flaw-shaped ``ScoreOutcome`` so the shared analyses could also be fed.
"""

from app.features.cs_eval.judge import AnswerJudgement, judge_answer
from app.features.cs_eval.questions import QUESTIONS
from app.harness.interface import ScoreOutcome


class CsEvalAdapter:
    name = "cs_eval"

    def __init__(self, model: str | None = None):
        self.model = model

    async def judge(self, question_index: int, answer_text: str) -> AnswerJudgement:
        """Judge one answer to a seeded question; the richer cs_eval outcome."""
        q = QUESTIONS[question_index]
        return await judge_answer(
            domain=q.domain,
            prompt_md=q.prompt_md,
            reference_answer=q.reference_answer,
            rubric=q.rubric,
            answer_text=answer_text,
        )

    async def score(self, problem_index: int, flaws: list[str]) -> ScoreOutcome:
        """Protocol shim: project the judgement onto the flaw-shaped outcome.

        ``flaws`` is the candidate answer (one string element). Keyword recall
        against the rubric's key_points maps onto ``recall``; the signed score
        onto ``weighted_score``.
        """
        answer_text = flaws[0] if flaws else ""
        q = QUESTIONS[problem_index]
        key_points = list((q.rubric or {}).get("key_points", []))
        judgement = await self.judge(problem_index, answer_text)
        matched = list(judgement.matched_keywords)
        recall = len(matched) / len(key_points) if key_points else 0.0
        return ScoreOutcome(
            gt_ids=key_points,
            matched_ids=matched,
            recall=recall,
            weighted_score=float(judgement.score),
        )

    async def pairwise(
        self, problem_index: int, flaws_a: list[str], flaws_b: list[str]
    ) -> str:
        raise NotImplementedError("cs_eval has no pairwise judge")
