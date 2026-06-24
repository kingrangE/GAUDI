"""Opt-in integration test hitting the real LLM. Skipped without a key."""

import os

import pytest

from app.features.cs_eval.judge import judge_answer

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"), reason="no OPENAI_API_KEY"
    ),
]


async def test_real_llm_scores_within_rubric():
    out = await judge_answer(
        domain="OS",
        prompt_md="프로세스와 스레드의 차이를 설명하세요.",
        reference_answer="프로세스는 독립 주소 공간을, 스레드는 공유 주소 공간을 가진다.",
        rubric={"key_points": ["프로세스는 독립 주소 공간", "스레드는 주소 공간 공유"]},
        answer_text="솔직히 잘 모르겠습니다.",
    )
    assert out.response_type in {"correct", "partial", "honest_unknown", "bluff_wrong"}
    assert -5 <= out.score <= 5
