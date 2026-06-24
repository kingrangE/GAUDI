"""Pure scoring math + the baseline keyword-overlap stub judge."""

from app.features.cs_eval import scoring
from app.features.cs_eval.judge import judge_answer, synthesize_reports

KEY_POINTS = ["해시 함수로 버킷 인덱스 계산", "충돌", "체이닝", "로드 팩터와 리해싱"]


def test_score_for_type_buckets():
    assert scoring.score_for_type("correct") == 5
    assert scoring.score_for_type("honest_unknown") == -2
    assert scoring.score_for_type("bluff_wrong") == -5
    assert scoring.score_for_type("partial", 3) == 3
    # partial is clamped into +1..+4
    assert scoring.score_for_type("partial", 9) == 4
    assert scoring.score_for_type("partial", 0) == 1


def test_normalize_maps_signed_total_to_0_100():
    # 4 questions → raw range [-20, +20].
    assert scoring.normalize(20, 4) == 100
    assert scoring.normalize(-20, 4) == 0
    assert scoring.normalize(0, 4) == 50
    assert scoring.normalize(5, 0) == 0  # guard against div-by-zero


def test_classify_correct_when_all_key_points_present():
    answer = " ".join(KEY_POINTS)
    rtype, matched, missing, partial = scoring.classify(answer, KEY_POINTS)
    assert rtype == "correct"
    assert missing == []
    assert partial is None


def test_classify_honest_unknown_for_blank_or_idk():
    assert scoring.classify("잘 모르겠습니다", KEY_POINTS)[0] == "honest_unknown"
    assert scoring.classify("", KEY_POINTS)[0] == "honest_unknown"


def test_classify_bluff_when_substantive_but_no_key_points():
    answer = "이것은 전혀 상관없는 장황한 설명이며 핵심을 비껴갑니다"
    rtype, matched, _missing, _ = scoring.classify(answer, KEY_POINTS)
    assert rtype == "bluff_wrong"
    assert matched == []


def test_classify_partial_for_some_matches():
    answer = "충돌이 발생하면 체이닝으로 해결합니다"
    rtype, matched, missing, partial = scoring.classify(answer, KEY_POINTS)
    assert rtype == "partial"
    assert matched and missing
    assert 1 <= partial <= 4


async def test_judge_answer_uses_rubric_key_points():
    judgement = await judge_answer(
        domain="자료구조",
        prompt_md="...",
        reference_answer="...",
        rubric={"key_points": KEY_POINTS},
        answer_text="잘 모르겠습니다",
    )
    assert judgement.response_type == "honest_unknown"
    assert judgement.score == -2
    assert set(judgement.missing_keywords) == set(KEY_POINTS)


async def test_synthesize_reports_surfaces_missing_keywords():
    reports = await synthesize_reports(
        per_question=[
            {
                "domain": "자료구조",
                "response_type": "partial",
                "score": 2,
                "matched_keywords": ["충돌"],
                "missing_keywords": ["체이닝", "로드 팩터와 리해싱"],
                "rationale": "일부만 짚음",
            }
        ]
    )
    assert "체이닝" in reports.summary_report
    assert "자료구조" in reports.analysis_report
