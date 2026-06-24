"""LLM judge: prompt grounding + structured-output schema (LLM mocked)."""

import pytest
from pydantic import ValidationError

from app.features.coding_test import judge as judge_mod
from app.features.coding_test.judge import JudgeOutput, judge_submission


async def test_judge_builds_grounded_prompt(monkeypatch):
    captured = {}

    async def fake_complete(system, user, schema):
        captured.update(system=system, user=user, schema=schema)
        return JudgeOutput(
            strengths=["s"], weaknesses=["w"], analysis_report="r", code_quality_score=70
        )

    monkeypatch.setattr(judge_mod, "complete_structured", fake_complete)

    out = await judge_submission(
        title="두 수의 합",
        description_md="설명",
        rubric={"key_concepts": ["해시맵"], "common_pitfalls": ["O(n^2)"]},
        reference_solution="def two_sum(nums, target): return [0, 1]",
        function_name="two_sum",
        code="def two_sum(nums, target): return []",
        test_passed=3,
        test_total=5,
        case_breakdown=[{"index": 0, "passed": True, "error": None}],
    )

    assert out.code_quality_score == 70
    assert captured["schema"] is JudgeOutput
    # the prompt is grounded on rubric + reference solution + the candidate code
    assert "해시맵" in captured["user"]
    assert "두 수의 합" in captured["user"]
    assert "def two_sum(nums, target): return [0, 1]" in captured["user"]
    assert '"passed": 3' in captured["user"]


def test_judge_output_rejects_out_of_range_score():
    with pytest.raises(ValidationError):
        JudgeOutput(strengths=[], weaknesses=[], analysis_report="r", code_quality_score=150)


def test_judge_output_requires_report():
    with pytest.raises(ValidationError):
        JudgeOutput(strengths=[], weaknesses=[], code_quality_score=50)
