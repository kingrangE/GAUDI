"""Admin read API + write contract over an in-memory DB (no LLM).

Seeds attempts through the service write contract, then asserts the admin
endpoints expose exactly the mock-exam data and nothing else.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.features.mock_exam import router as mock_exam_router
from app.features.mock_exam import service

CODE_A = "AY-7F3K9Q"
CODE_B = "AY-4M8X2P"

# A native result blob per feature, shaped like each feature's real scorer.
FEATURE_RESULTS = {
    "test_design": {"weighted_score": 0.6, "recall": 0.5},
    "dev_prompting": {"total": 0.8},
    "spec_design": {"total": 70},
    "rejection_eval": {"f1": 0.9},
    "context_engineering": {"total": 50},
}
# Means to 70.0 (60+80+70+90+50)/5.
EXPECTED_OVERALL = 70.0


@pytest_asyncio.fixture
async def db(engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session


async def _seed_completed_attempt(db, code=CODE_A):
    attempt = await service.create_exam_attempt(db, code)
    for feature_key, raw in FEATURE_RESULTS.items():
        await service.record_feature_result(db, attempt.id, feature_key, raw)
    return await service.finalize_exam_attempt(db, attempt.id)


async def test_finalize_averages_feature_scores(db):
    attempt = await _seed_completed_attempt(db)
    assert attempt.status == "completed"
    assert attempt.completed_at is not None
    assert attempt.overall_normalized == EXPECTED_OVERALL


async def test_record_is_idempotent_per_feature(db):
    attempt = await service.create_exam_attempt(db, CODE_A)
    await service.record_feature_result(db, attempt.id, "spec_design", {"total": 40})
    await service.record_feature_result(db, attempt.id, "spec_design", {"total": 90})
    finalized = await service.finalize_exam_attempt(db, attempt.id)
    # Second recording overwrote the first — only one feature row, score 90.
    assert finalized.overall_normalized == 90.0
    detail = await service.get_exam_result(db, attempt.id)
    assert len(detail.features) == 1


async def test_create_rejects_unknown_candidate(db):
    with pytest.raises(ValueError, match="unknown candidate code"):
        await service.create_exam_attempt(db, "NOT-A-CODE")


async def test_record_rejects_non_mock_exam_feature(db):
    attempt = await service.create_exam_attempt(db, CODE_A)
    with pytest.raises(ValueError, match="not a mock-exam feature"):
        await service.record_feature_result(db, attempt.id, "cs_eval", {"total": 1})


async def test_candidates_endpoint_lists_three_with_latest(client, db):
    await _seed_completed_attempt(db, CODE_A)

    resp = await client.get("/api/admin/candidates")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3  # always the three fixed candidates

    by_code = {c["code"]: c for c in body}
    assert by_code[CODE_A]["latest_attempt"]["overall_normalized"] == EXPECTED_OVERALL
    # A candidate who never took the mock exam has no attempt (practice excluded).
    assert by_code[CODE_B]["latest_attempt"] is None


async def test_exam_results_list_and_detail(client, db):
    attempt = await _seed_completed_attempt(db, CODE_A)

    listing = await client.get("/api/admin/exam-results")
    assert listing.status_code == 200
    rows = listing.json()
    assert len(rows) == 1
    assert rows[0]["candidate_label"] == "응시자 A"
    assert rows[0]["feature_count"] == 5

    detail = await client.get(f"/api/admin/exam-results/{attempt.id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["overall_normalized"] == EXPECTED_OVERALL
    features = {f["feature_key"]: f for f in payload["features"]}
    assert set(features) == set(FEATURE_RESULTS)
    assert features["rejection_eval"]["normalized_score"] == 90.0
    assert features["test_design"]["label"] == "테스트 설계"
    # Native blob is preserved for the detail view.
    assert features["test_design"]["raw_result"]["recall"] == 0.5


async def test_detail_404_for_unknown_attempt(client):
    resp = await client.get("/api/admin/exam-results/deadbeef")
    assert resp.status_code == 404


async def test_admin_token_guard(client, monkeypatch):
    class _Settings:
        admin_token = "s3cret"

    monkeypatch.setattr(mock_exam_router, "get_settings", lambda: _Settings())

    denied = await client.get("/api/admin/exam-results")
    assert denied.status_code == 401

    allowed = await client.get(
        "/api/admin/exam-results", headers={"X-Admin-Token": "s3cret"}
    )
    assert allowed.status_code == 200
