"""Opt-in integration test: the real OpenAI judge end-to-end.

Skipped unless OPENAI_API_KEY is exported. Asserts only on shape/bounds, never
on exact model wording. Run explicitly with: pytest -m integration
"""

import os

import pytest

from app.features.coding_test.judge import judge_submission

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="no OPENAI_API_KEY"),
]


async def test_real_judge_smoke():
    out = await judge_submission(
        title="두 수의 합",
        description_md="더해서 target이 되는 두 인덱스를 오름차순으로 반환하세요.",
        rubric={"key_concepts": ["해시맵"], "expected_complexity": "O(n)"},
        reference_solution="def two_sum(nums, target):\n    ...\n",
        function_name="two_sum",
        code="def two_sum(nums, target):\n    return []\n",  # wrong on purpose
        test_passed=0,
        test_total=5,
        case_breakdown=[{"index": 0, "passed": False, "error": "wrong_answer"}],
    )
    assert 0 <= out.code_quality_score <= 100
    assert out.analysis_report
    assert isinstance(out.strengths, list)
    assert isinstance(out.weaknesses, list)
