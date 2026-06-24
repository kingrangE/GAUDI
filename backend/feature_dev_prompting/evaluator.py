"""Multi-turn orchestration: prompt -> code -> run -> grade, with feedback between turns.

The candidate never edits code; each turn is a prompt. We stop early once solved and
score the run via the grader. The LLM call and the code runner are both injectable so
unit tests can mock them.
"""

from __future__ import annotations

from feature_dev_prompting.grader import evaluation_score, summarize_run
from feature_dev_prompting.models import CaseResult, EvaluationResult, Problem, TurnResult
from feature_dev_prompting.sandbox import run_against_tests
from feature_dev_prompting.solver import generate_code
from llm.client import LLMClient, get_llm_client


def build_feedback(case_results: list[CaseResult]) -> str:
    """Human-readable feedback for the next turn. Hidden cases are counted only."""

    public = [c for c in case_results if not c.hidden]
    hidden = [c for c in case_results if c.hidden]
    pub_pass = sum(1 for c in public if c.passed)
    hidden_failed = sum(1 for c in hidden if not c.passed)

    lines = [f"공개 예제 {pub_pass}/{len(public)} 통과, 숨김 테스트 실패 {hidden_failed}개."]
    for c in public:
        if not c.passed:
            lines.append(f"- 예제 #{c.index}: 기대={c.expected!r}, 실제={c.got!r} ({c.status})")
    return "\n".join(lines)


def evaluate(problem: Problem, prompts: list[str], *, client: LLMClient | None = None,
             runner=run_against_tests, max_turns: int | None = None) -> EvaluationResult:
    """Run the candidate's prompts turn by turn and return the scored result."""

    client = client or get_llm_client()
    limit = max_turns if max_turns is not None else len(prompts)

    turns: list[TurnResult] = []
    feedback: str | None = None
    current_code = problem.starter_code  # the function as it currently stands; edited each turn
    for idx, prompt in enumerate(prompts[:limit], start=1):
        code = generate_code(client, problem, prompt, current_code, feedback)
        case_results = runner(
            code, problem.tests, problem.entry_point, time_limit=problem.time_limit_sec
        )
        passed, total = summarize_run(case_results)
        solved = total > 0 and passed == total
        feedback = build_feedback(case_results)
        turns.append(
            TurnResult(
                turn=idx,
                prompt=prompt,
                code=code,
                passed_count=passed,
                total=total,
                solved=solved,
                feedback=feedback,
                case_results=case_results,
            )
        )
        current_code = code  # next turn edits whatever the agent just produced
        if solved:
            break

    score = evaluation_score(turns)
    return EvaluationResult(problem_id=problem.id, solved=score.solved, score=score, turns=turns)
