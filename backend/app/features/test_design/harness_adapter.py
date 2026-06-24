"""test_design's implementation of the harness `JudgeAdapter`.

Wraps the live LLM judge + deterministic scoring behind the harness interface so
the reliability analyses can run against this feature. A specific judge model
can be pinned (for the self-preference sweep); otherwise the centralized
``settings.llm_model`` is used.
"""

from dataclasses import asdict

from app.features.test_design import scoring
from app.features.test_design.judging import judge_pairwise, judge_submission
from app.features.test_design.problems import get_problem
from app.harness.interface import ScoreOutcome


class TestDesignAdapter:
    __test__ = False  # not a pytest test class despite the 'Test' prefix
    name = "test_design"

    def __init__(self, model: str | None = None):
        self.model = model

    async def score(self, problem_index: int, flaws: list[str]) -> ScoreOutcome:
        problem = get_problem(problem_index)
        judged = await judge_submission(problem, flaws, model=self.model)
        gt_flaws = [asdict(f) for f in problem.flaws]
        matches = [m.model_dump() for m in judged.matches]
        result = scoring.score_submission(gt_flaws, flaws, matches, report=judged.report)
        return ScoreOutcome(
            gt_ids=[f.id for f in problem.flaws],
            matched_ids=[f["id"] for f in result["flaws"] if f["found"]],
            recall=result["recall"],
            precision=result["precision"],
            weighted_score=result["weighted_score"],
            mean_quality=result["mean_quality"],
        )

    async def pairwise(
        self, problem_index: int, flaws_a: list[str], flaws_b: list[str]
    ) -> str:
        problem = get_problem(problem_index)
        verdict = await judge_pairwise(problem, flaws_a, flaws_b, model=self.model)
        return verdict.winner
