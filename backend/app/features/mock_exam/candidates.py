"""The three fixed mock-exam candidates and the five mock-exam features.

The candidate codes mirror the frontend's pre-shared entry codes
(`frontend/src/lib/accessCodes.ts` `USER_CODES`) — keep both lists in sync.
There is no auth yet; the code IS the candidate identity.

The mock exam is the practice feature set MINUS the three excluded tracks
(CS deep-eval, traditional coding test, office prompting).
"""

from __future__ import annotations

# code -> human-facing label shown in the admin console.
CANDIDATES: dict[str, str] = {
    "AY-7F3K9Q": "응시자 A",
    "AY-4M8X2P": "응시자 B",
    "AY-6B5T3R": "응시자 C",
}

# feature_key -> label. Order defines the canonical display order and the set
# of features a *complete* mock-exam attempt is expected to contain.
MOCK_EXAM_FEATURES: dict[str, str] = {
    "test_design": "테스트 설계",
    "dev_prompting": "개발 프롬프팅",
    "spec_design": "명세 설계",
    "rejection_eval": "AI 거부 능력",
    "context_engineering": "컨텍스트 엔지니어링",
}


def candidate_label(code: str) -> str:
    """Display label for a candidate code (falls back to the raw code)."""
    return CANDIDATES.get(code, code)


def is_candidate(code: str) -> bool:
    return code in CANDIDATES


def is_mock_exam_feature(feature_key: str) -> bool:
    return feature_key in MOCK_EXAM_FEATURES


def feature_label(feature_key: str) -> str:
    return MOCK_EXAM_FEATURES.get(feature_key, feature_key)
