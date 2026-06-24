"""Opt-in integration test: a real OpenAI judge call.

Skipped unless OPENAI_API_KEY is set, so the default CI suite stays green
without a key. Run locally with a key to sanity-check the live judge.
"""

import os

import pytest

from app.features.test_design.harness_adapter import TestDesignAdapter

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="needs OPENAI_API_KEY"),
]


async def test_real_judge_scores_a_problem():
    adapter = TestDesignAdapter()
    outcome = await adapter.score(
        0, ["파일 크기 상한이 없어 거대한 파일을 올려 스토리지를 고갈시킬 수 있다"]
    )
    assert 0.0 <= outcome.recall <= 1.0
    assert set(outcome.matched_ids) <= set(outcome.gt_ids)
