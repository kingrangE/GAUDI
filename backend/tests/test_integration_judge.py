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
    outcome = await adapter.score(0, ["빈 리스트를 넣으면 0으로 나눠 ZeroDivisionError가 난다"])
    assert 0.0 <= outcome.recall <= 1.0
    assert set(outcome.matched_ids) <= set(outcome.gt_ids)
