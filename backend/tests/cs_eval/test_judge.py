"""LLM judge with `complete_structured` mocked (offline, deterministic)."""

from app.features.cs_eval import judge as judge_mod
from app.features.cs_eval.judge import judge_answer, synthesize_reports


def test_system_prompt_distinguishes_honesty_from_bluff():
    assert "honest_unknown" in judge_mod._SYSTEM
    assert "bluff_wrong" in judge_mod._SYSTEM
    assert "허세" in judge_mod._SYSTEM


async def test_judge_answer_reconciles_score_to_type(monkeypatch):
    captured = {}

    async def fake_complete(system, user, schema):
        captured["user"] = user
        # LLM says "partial" but with a score above the partial cap → reconciled.
        return schema(
            response_type="partial",
            score=5,
            matched_keywords=["충돌"],
            missing_keywords=["체이닝"],
            rationale="일부만 설명",
        )

    monkeypatch.setattr(judge_mod, "complete_structured", fake_complete)
    out = await judge_answer(
        domain="자료구조",
        prompt_md="해시 테이블?",
        reference_answer="모범답안",
        rubric={"key_points": ["충돌", "체이닝"]},
        answer_text="충돌이 발생합니다",
    )
    assert out.response_type == "partial"
    assert out.score == 4  # 5 clamped into the partial bucket (+1..+4)
    # rubric + reference answer are grounded into the prompt
    assert "체이닝" in captured["user"]
    assert "모범답안" in captured["user"]


async def test_judge_answer_honest_unknown_is_minus_two(monkeypatch):
    async def fake_complete(system, user, schema):
        # Even if the LLM returns 0, the rubric bucket pins honest_unknown to −2.
        return schema(
            response_type="honest_unknown",
            score=0,
            matched_keywords=[],
            missing_keywords=["x"],
            rationale="모름 인정",
        )

    monkeypatch.setattr(judge_mod, "complete_structured", fake_complete)
    out = await judge_answer(
        domain="OS",
        prompt_md="q",
        reference_answer="",
        rubric={"key_points": ["x"]},
        answer_text="잘 모르겠습니다",
    )
    assert out.score == -2


async def test_synthesize_reports(monkeypatch):
    async def fake_complete(system, user, schema):
        assert "per_question" in user
        return schema(summary_report="부족: 체이닝", analysis_report="네다섯 문장 진단")

    monkeypatch.setattr(judge_mod, "complete_structured", fake_complete)
    reports = await synthesize_reports(
        per_question=[
            {
                "domain": "자료구조",
                "response_type": "partial",
                "score": 2,
                "matched_keywords": ["충돌"],
                "missing_keywords": ["체이닝"],
                "rationale": "r",
            }
        ]
    )
    assert reports.summary_report and reports.analysis_report
