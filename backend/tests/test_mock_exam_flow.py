"""Candidate-facing mock-exam orchestration (`/api/mock-exam`).

Covers the thin chaining layer end-to-end with every LLM seam mocked:
- the full 5-step happy path (one attempt, single timer, per-step submit),
- that no candidate-facing response leaks a score, and generate hides `is_flawed`,
- that finish averages the recorded per-feature scores, and
- that an unknown attempt / candidate fails loudly.

All five features score server-side; here we patch each feature's LLM call
(rejection generate+judge, spec evaluator, dev evaluator) and force the
context judge / dev solver to the keyless path so the suite stays hermetic.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.features.mock_exam import exam_router
from app.features.mock_exam.exam_router import (
    EXAM_FLOW,
    EXAM_TOTAL_SECONDS,
    get_context_client,
    get_solver_client,
)
from app.features.rejection_eval import service as rej_service
from app.features.rejection_eval.schemas import (
    GeneratedItem,
    GenerationOutput,
    ItemJudgement,
    JudgeOutput,
)
from app.main import app

CANDIDATE = "AY-7F3K9Q"

# Keys that must never appear in any candidate-facing response.
_FORBIDDEN = {"score", "grade", "f1", "precision", "recall", "weighted_score", "verdict"}

# One non-empty input per step so each adapter's `_require` guard passes.
_STEP_INPUT: dict[str, dict] = {
    "context_engineering": {"claude_md": "# cx-churn-radar\nProject guide for the agent."},
    "spec_design": {"instruction": "Build a top-N churn API with pagination and auth."},
    "rejection_eval": {"flagged_ids": ["item-1"], "reasons": {"item-1": "wrong datastore"}},
    "test_design": {"flaws": ["missing input validation on the limit param"]},
    "dev_prompting": {"prompts": ["Stream churn events and keep a running top-N heap."]},
}


# --------------------------------------------------------------------------- #
# Fake feature results (carry the one field normalize.py requires + score.total)
# --------------------------------------------------------------------------- #
class _FakeSpecResult:
    def __init__(self, total: float) -> None:
        self.score = SimpleNamespace(total=total)

    def model_dump(self) -> dict:
        # No top-level "total" — the adapter copies score.total up to raw["total"].
        return {"total_score": self.score.total, "score": {"total": self.score.total}}


class _FakeDevResult:
    def __init__(self, total: float) -> None:
        self.score = SimpleNamespace(total=total)  # 0–100; adapter scales to 0–1

    def model_dump(self) -> dict:
        return {"solved": True, "score": {"total": self.score.total}}


@pytest.fixture
def mock_all_llm(monkeypatch, mock_judge):
    """Patch every feature's LLM seam (rejection / spec / dev) and force the
    context judge + dev solver onto the keyless path. `mock_judge` (conftest)
    covers the test_design judge."""

    async def fake_generate_design(topic_title, prompt):
        return GenerationOutput(
            items=[
                GeneratedItem(
                    id="item-1", text="Use a fresh NoSQL store", is_flawed=True,
                    flaw_type="wrong_tech", explanation="hidden",
                ),
                GeneratedItem(
                    id="item-2", text="Return the top-N by churn score", is_flawed=False,
                    flaw_type="none", explanation="hidden",
                ),
            ]
        )

    async def fake_judge_attempt(requirements, items, flagged_ids, reasons):
        return JudgeOutput(
            report="stub",
            judgements=[
                ItemJudgement(item_id=i.id, in_requirements=(i.id == "item-2"))
                for i in items
            ],
        )

    async def fake_spec_evaluate(task, instruction):
        return _FakeSpecResult(total=80.0)

    def fake_dev_evaluate(problem, prompts, *, client=None, **kwargs):
        return _FakeDevResult(total=90.0)

    monkeypatch.setattr(rej_service, "generate_design", fake_generate_design)
    monkeypatch.setattr(rej_service, "judge_attempt", fake_judge_attempt)
    monkeypatch.setattr(exam_router, "spec_evaluate", fake_spec_evaluate)
    monkeypatch.setattr(exam_router, "dev_evaluate", fake_dev_evaluate)

    app.dependency_overrides[get_context_client] = lambda: None
    app.dependency_overrides[get_solver_client] = lambda: object()
    yield
    app.dependency_overrides.pop(get_context_client, None)
    app.dependency_overrides.pop(get_solver_client, None)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _assert_no_scores(payload) -> None:
    """Recursively assert no forbidden score key appears anywhere in a response."""
    if isinstance(payload, dict):
        leaked = _FORBIDDEN & payload.keys()
        assert not leaked, f"candidate response leaked score keys: {leaked}"
        for value in payload.values():
            _assert_no_scores(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_scores(value)


async def _run_full_flow(client) -> tuple[str, list[dict]]:
    """Drive start -> all five submits (no finish). Returns the attempt id and
    every candidate-facing response collected along the way."""
    seen: list[dict] = []

    start = await client.post("/api/mock-exam/start", json={"candidate_code": CANDIDATE})
    assert start.status_code == 200, start.text
    body = start.json()
    seen.append(body)
    attempt_id = body["attempt_id"]
    assert body["flow"] == EXAM_FLOW
    assert body["current_step"] == EXAM_FLOW[0]
    assert 0 < body["remaining_seconds"] <= EXAM_TOTAL_SECONDS

    for step in EXAM_FLOW:
        material = await client.get(f"/api/mock-exam/attempts/{attempt_id}/steps/{step}")
        assert material.status_code == 200, material.text
        seen.append(material.json())

        if step == "rejection_eval":
            gen = await client.post(
                f"/api/mock-exam/attempts/{attempt_id}/steps/rejection_eval/generate",
                json={"prompt": "Design a churn top-N API."},
            )
            assert gen.status_code == 200, gen.text
            gen_body = gen.json()
            seen.append(gen_body)
            # generate exposes only public {id, text}; is_flawed/explanation hidden.
            assert gen_body["items"]
            for item in gen_body["items"]:
                assert set(item.keys()) == {"id", "text"}

        submit = await client.post(
            f"/api/mock-exam/attempts/{attempt_id}/steps/{step}/submit",
            json=_STEP_INPUT[step],
        )
        assert submit.status_code == 200, submit.text
        seen.append(submit.json())

    return attempt_id, seen


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_full_flow_happy_path(client, mock_all_llm):
    attempt_id, seen = await _run_full_flow(client)

    # Each submit acknowledges only {recorded, next_step}; next_step advances the
    # flow and is None after the last step.
    submits = [s for s in seen if set(s.keys()) == {"recorded", "next_step"}]
    assert len(submits) == len(EXAM_FLOW)
    expected_next = EXAM_FLOW[1:] + [None]
    for ack, nxt in zip(submits, expected_next):
        assert ack["recorded"] is True
        assert ack["next_step"] == nxt

    state = await client.get(f"/api/mock-exam/attempts/{attempt_id}")
    assert state.status_code == 200
    state_body = state.json()
    assert state_body["completed_steps"] == EXAM_FLOW
    assert state_body["current_step"] is None

    finish = await client.post(f"/api/mock-exam/attempts/{attempt_id}/finish")
    assert finish.status_code == 200
    assert finish.json() == {"completed": True}


@pytest.mark.asyncio
async def test_candidate_responses_hide_scores(client, mock_all_llm):
    _, seen = await _run_full_flow(client)
    for payload in seen:
        _assert_no_scores(payload)


@pytest.mark.asyncio
async def test_finish_averages_recorded_scores(client, mock_all_llm):
    attempt_id, _ = await _run_full_flow(client)
    await client.post(f"/api/mock-exam/attempts/{attempt_id}/finish")

    # The admin read API exposes the server-side scores the candidate never saw.
    detail = await client.get(f"/api/admin/exam-results/{attempt_id}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["status"] == "completed"
    assert {f["feature_key"] for f in body["features"]} == set(EXAM_FLOW)

    scores = [f["normalized_score"] for f in body["features"]]
    assert all(0.0 <= s <= 100.0 for s in scores)
    assert body["overall_normalized"] == pytest.approx(round(sum(scores) / len(scores), 1))


@pytest.mark.asyncio
async def test_unknown_attempt_returns_404(client, mock_all_llm):
    missing = "deadbeef"
    assert (await client.get(f"/api/mock-exam/attempts/{missing}")).status_code == 404
    assert (
        await client.get(f"/api/mock-exam/attempts/{missing}/steps/spec_design")
    ).status_code == 404
    submit = await client.post(
        f"/api/mock-exam/attempts/{missing}/steps/spec_design/submit",
        json=_STEP_INPUT["spec_design"],
    )
    assert submit.status_code == 404


@pytest.mark.asyncio
async def test_start_rejects_unknown_candidate(client):
    resp = await client.post("/api/mock-exam/start", json={"candidate_code": "NOPE"})
    assert resp.status_code == 400
