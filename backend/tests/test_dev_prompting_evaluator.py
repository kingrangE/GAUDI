"""Multi-turn evaluator loop. LLM is mocked via a fake client; sandbox runs for real."""

from feature_dev_prompting.evaluator import build_feedback, evaluate
from feature_dev_prompting.models import CaseResult
from feature_dev_prompting.problems import get_problem

CORRECT_SUM = (
    "from collections import deque\n"
    "def solution(stones, k):\n"
    "    dq = deque()\n"
    "    res = float('inf')\n"
    "    for i, v in enumerate(stones):\n"
    "        while dq and stones[dq[-1]] <= v:\n"
    "            dq.pop()\n"
    "        dq.append(i)\n"
    "        if dq[0] <= i - k:\n"
    "            dq.popleft()\n"
    "        if i >= k - 1:\n"
    "            res = min(res, stones[dq[0]])\n"
    "    return res\n"
)
WRONG = "def solution(stones, k):\n    return 0\n"


class FakeClient:
    """Returns the next canned code per call; last entry repeats."""

    def __init__(self, codes):
        self._codes = list(codes)
        self.calls = []

    def complete(self, system, user):
        self.calls.append((system, user))
        return self._codes[min(len(self.calls) - 1, len(self._codes) - 1)]


def test_single_shot_solved():
    problem = get_problem("stepping-stones")
    res = evaluate(problem, ["배열의 합을 구해줘"], client=FakeClient([CORRECT_SUM]))
    assert res.solved is True
    assert res.score.total == 100.0
    assert len(res.turns) == 1


def test_multiturn_solves_on_second_turn_with_feedback():
    problem = get_problem("stepping-stones")
    client = FakeClient([WRONG, CORRECT_SUM])
    res = evaluate(problem, ["일단 풀어봐", "sum 으로 고쳐"], client=client)
    assert res.solved is True
    assert res.score.solved_turn == 2
    assert len(res.turns) == 2
    assert res.turns[0].solved is False
    # the 2nd solver call received the previous turn's feedback
    assert "피드백" in client.calls[1][1]


def test_unsolved_after_max_turns():
    problem = get_problem("stepping-stones")
    res = evaluate(problem, ["a", "b", "c"], client=FakeClient([WRONG]), max_turns=2)
    assert res.solved is False
    assert len(res.turns) == 2
    assert res.score.understanding_score == 0.0


def test_build_feedback_reveals_public_only():
    crs = [
        CaseResult(index=0, hidden=False, passed=False, status="wrong_answer",
                   expected="6", got="0"),
        CaseResult(index=1, hidden=True, passed=False, status="wrong_answer"),
    ]
    fb = build_feedback(crs)
    assert "예제 #0" in fb
    assert "숨김 테스트 실패 1개" in fb
    assert "기대='6'" in fb
