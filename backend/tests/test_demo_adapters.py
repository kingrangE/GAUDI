"""Native flows through real job adapters; LLM/runner seams remain deterministic."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_demo_jobs import FakeQueue
from test_mock_exam_flow import _STEP_INPUT, _assert_no_scores, mock_all_llm  # noqa: F401

from app.core.config import get_settings
from app.features.mock_exam import exam_router
from app.features.mock_exam.models import ExamAttempt
from app.main import app
from feature_demo import dispatch
from feature_demo.models import DemoJob, DemoResource
from feature_demo.operations import OPERATIONS
from feature_demo.worker import run_job


@pytest.fixture
async def demo(client, engine, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_enabled", True)
    monkeypatch.setattr(get_settings(), "demo_cookie_secure", False)
    queue = FakeQueue()
    monkeypatch.setattr(dispatch, "get_demo_queue", lambda: queue)
    await client.post("/api/demo/session")
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def invoke(path, body=None, key=None):
        response = await client.post(
            path, json=body or {}, headers={"Idempotency-Key": key or uuid4().hex}
        )
        assert response.status_code == 202, response.text
        job_id = response.json()["job_id"]
        assert response.json()["status"] == "queued"
        await run_job(job_id, maker)
        state = (await client.get(f"/api/demo/jobs/{job_id}")).json()
        assert state["status"] == "completed", (path, state)
        result = (await client.get(f"/api/demo/jobs/{job_id}/result")).json()
        return result["body"], job_id

    return invoke, maker, queue


def test_every_native_mutation_is_allowlisted():
    prefixes = (
        "/api/coding-test",
        "/api/cs-eval",
        "/api/mock-exam",
        "/test-design",
        "/dev-prompting",
        "/spec-design",
        "/api/rejection-eval",
        "/api/office-prompting",
        "/api/context-engineering",
    )
    paths = {
        path
        for path, methods in app.openapi()["paths"].items()
        if path.startswith(prefixes) and "post" in methods
    }
    assert paths == {operation.path for operation in OPERATIONS}


@pytest.mark.parametrize("path", [operation.path for operation in OPERATIONS])
async def test_headers_cannot_bypass_job_ingress(client, demo, path):
    # Even a valid cookie/admin token cannot turn HTTP headers into a worker execution context.
    response = await client.post(
        path.format(
            session_id="x",
            run_id="x",
            attempt_id="x",
            topic_index=0,
            problem_index=0,
            problem_id="x",
            feature_key="context_engineering",
        ),
        json={},
        headers={"X-Demo-Worker": "true"},
    )
    assert response.status_code == 428


async def test_native_context_and_specification_keep_real_report_contract(
    client, demo, monkeypatch
):
    from feature_spec_design.api import get_gen_dependency, get_judge_dependency
    from feature_spec_design.tasks import list_tasks

    invoke, maker, _ = demo
    report, job_id = await invoke(
        "/api/context-engineering/submissions",
        {
            "project_id": "todo-api",
            "claude_md": "`app/main.py` and `make test`",
        },
    )
    assert report["scored"] and report["project_id"] == "todo-api"
    calls = []

    class Client:
        def complete(self, *args, **kwargs):
            calls.append(1)
            return '{"requirements_met": [], "decisions": {}, "extra_scope": []}'

    app.dependency_overrides[get_gen_dependency] = lambda: Client()
    app.dependency_overrides[get_judge_dependency] = lambda: Client()
    monkeypatch.setenv("SPEC_SAMPLES", "2")
    report, job_id = await invoke(
        "/spec-design/evaluate",
        {
            "task_id": list_tasks()[0].id,
            "instruction": "명시된 요구사항만 구현",
        },
    )
    assert len(report["samples"]) == 2
    assert len(calls) == 4
    async with maker() as db:
        job = await db.get(DemoJob, job_id)
        assert job.completed_units == job.total_units == 5


async def test_test_design_and_rejection_use_native_scoring_and_hide_generated_truth(
    client,
    demo,
    mock_judge,
    monkeypatch,
):
    from app.features.rejection_eval import service
    from app.features.rejection_eval.schemas import GenerationOutput, JudgeOutput

    invoke, _, _ = demo
    session, _ = await invoke("/test-design/sessions", {"candidate_name": "visitor"})
    response, _ = await invoke(
        f"/test-design/sessions/{session['session_id']}/problems/0/submit", {"flaws": ["빈 입력"]}
    )
    assert response["submitted"]
    report = (await client.get(f"/test-design/sessions/{session['session_id']}/result")).json()
    assert len(report["problems"]) == 1

    async def generate(*args):
        return GenerationOutput(
            items=[
                dict(
                    id="a", text="설계", is_flawed=True, flaw_type="wrong_tech", explanation="정답"
                )
            ]
        )

    async def judge(*args):
        return JudgeOutput(report="분석", judgements=[{"item_id": "a", "in_requirements": True}])

    monkeypatch.setattr(service, "generate_design", generate)
    monkeypatch.setattr(service, "judge_attempt", judge)
    session, _ = await invoke("/api/rejection-eval/sessions")
    base = f"/api/rejection-eval/sessions/{session['session_id']}"
    generated, _ = await invoke(base + "/topics/0/generate", {"prompt": "지시"})
    assert generated["items"] == [{"id": "a", "text": "설계"}]
    await invoke(base + "/topics/0/submit", {"flagged_ids": ["a"]})
    report, _ = await invoke(base + "/score")
    assert report["f1"] == 1


async def test_office_full_flow_preserves_runs_and_result_contract(client, demo, monkeypatch):
    from app.features.office_prompting import service
    from app.features.office_prompting.problems import PROBLEMS
    from app.features.office_prompting.schemas import ExtractionOutput

    async def extract(problem, prompt):
        return ExtractionOutput(ids=list(problem.ground_truth_ids))

    monkeypatch.setattr(service, "extract_ids", extract)
    invoke, _, _ = demo
    session, _ = await invoke("/api/office-prompting/sessions", {"candidate_name": "visitor"})
    base = f"/api/office-prompting/sessions/{session['session_id']}"
    for problem in PROBLEMS:
        run, _ = await invoke(base + f"/problems/{problem.index}/run", {"prompt": "조건"})
        assert "truth_ids" not in run and "f1" not in run
    report, _ = await invoke(base + "/score")
    assert report["f1"] == 1


async def test_development_turns_are_generated_once_and_owned(client, demo, monkeypatch):
    from feature_dev_prompting import sessions
    from feature_dev_prompting.api import get_solver_client
    from feature_dev_prompting.models import TurnResult

    calls = []

    def generate(problem, turns, prompt, solver):
        calls.append(prompt)
        return TurnResult(
            turn=1,
            prompt=prompt,
            code="def solution(): pass",
            passed_count=1,
            total=1,
            solved=True,
            feedback="ok",
            case_results=[],
        )

    monkeypatch.setattr(sessions, "execute_turn", generate)
    app.dependency_overrides[get_solver_client] = lambda: object()
    invoke, maker, _ = demo
    run, _ = await invoke("/dev-prompting/runs", {"problem_id": "stepping-stones"})
    path = f"/dev-prompting/runs/{run['run_id']}/turns"
    key = uuid4().hex
    result, job_id = await invoke(path, {"prompt": "지시", "turn": 1}, key)
    repeated = await client.post(
        path, json={"prompt": "지시", "turn": 1}, headers={"Idempotency-Key": key}
    )
    assert repeated.json()["job_id"] == job_id
    assert result["turns"][0]["prompt"] == "지시" and calls == ["지시"]
    async with maker() as db:
        assert await db.get(DemoResource, ("dev_prompting", run["run_id"]))


async def test_coding_and_cs_run_inline_inside_worker_even_when_rq_enabled(
    client, demo, monkeypatch
):
    from coding_test.conftest import InProcessRunner, _fake_judge
    from cs_eval.conftest import _stub_judge_answer, _stub_synthesize

    from app.features.coding_test import grading as code_grading
    from app.features.coding_test import service as code_service
    from app.features.coding_test.problems import PROBLEMS
    from app.features.cs_eval import grading as cs_grading
    from app.features.cs_eval.questions import QUESTIONS
    from app.scripts.seed_cs_questions import _upsert as seed_question
    from app.scripts.seed_problems import _upsert as seed_problem

    monkeypatch.setattr(get_settings(), "grading_mode", "rq")
    monkeypatch.setattr(code_service, "runner", InProcessRunner())
    monkeypatch.setattr(code_grading, "judge_submission", _fake_judge)
    monkeypatch.setattr(cs_grading, "judge_answer", _stub_judge_answer)
    monkeypatch.setattr(cs_grading, "synthesize_reports", _stub_synthesize)
    invoke, maker, queue = demo
    async with maker() as db:
        await seed_problem(db, PROBLEMS[0])
        for question in QUESTIONS[:2]:
            await seed_question(db, question)
        await db.commit()
    sample, _ = await invoke(f"/api/coding-test/problems/{PROBLEMS[0].id}/run", {"code": "pass"})
    assert "results" in sample
    submission, _ = await invoke(
        "/api/coding-test/submissions",
        {
            "problem_id": PROBLEMS[0].id,
            "candidate_id": "visitor",
            "code": "pass",
        },
    )
    assert (await client.get(f"/api/coding-test/submissions/{submission['submission_id']}")).json()[
        "status"
    ] == "graded"
    session, _ = await invoke(
        "/api/cs-eval/sessions",
        {
            "candidate_id": "visitor",
            "answers": [
                {"question_id": question.id, "answer_text": "모름"} for question in QUESTIONS[:2]
            ],
        },
    )
    assert (await client.get(f"/api/cs-eval/sessions/{session['session_id']}")).json()[
        "status"
    ] == "graded"
    assert all(target == "feature_demo.worker.execute" for target, _, _ in queue.calls)


async def test_exam_uses_acceptance_time_and_job_result_never_reveals_scores(
    client, demo, monkeypatch
):
    invoke, maker, _ = demo
    app.dependency_overrides[exam_router.get_context_client] = lambda: None
    attempt, _ = await invoke("/api/mock-exam/start", {"candidate_code": "ignored"})
    path = f"/api/mock-exam/attempts/{attempt['attempt_id']}"
    response = await client.post(
        path + "/steps/context_engineering/submit",
        json={"claude_md": "`app/main.py`"},
        headers={"Idempotency-Key": uuid4().hex},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    # The answer was accepted before the deadline but the queue waited past it.
    async with maker() as db:
        saved_job = await db.get(DemoJob, job_id)
        attempt_row = await db.get(ExamAttempt, attempt["attempt_id"])
        started = datetime.now(timezone.utc) - timedelta(seconds=3601)
        attempt_row.started_at = started
        saved_job.created_at = started + timedelta(seconds=3599)
        await db.commit()
    await run_job(job_id, maker)
    state = (await client.get(f"/api/demo/jobs/{job_id}")).json()
    assert state["status"] == "completed", (path, state)
    result = (await client.get(f"/api/demo/jobs/{job_id}/result")).json()["body"]
    assert result["recorded"] and set(result) == {"recorded", "next_step"}
    late = await client.post(
        path + "/steps/spec_design/submit",
        json={"instruction": "late"},
        headers={"Idempotency-Key": uuid4().hex},
    )
    assert late.status_code == 409


async def test_job_submission_cannot_target_another_visitors_native_resource(client, demo):
    invoke, _, _ = demo
    session, _ = await invoke("/test-design/sessions", {"candidate_name": "visitor"})
    client.cookies.clear()
    await client.post("/api/demo/session")
    response = await client.post(
        "/api/demo/jobs",
        json={
            "feature": "test_design",
            "action": "submit",
            "input": {
                "params": {"session_id": session["session_id"], "problem_index": 0},
                "body": {"flaws": ["x"]},
            },
        },
        headers={"Idempotency-Key": uuid4().hex},
    )
    assert response.status_code == 404


@pytest.mark.usefixtures("mock_all_llm")
async def test_mock_exam_all_five_steps_finish_and_retry_keep_public_contract(client, demo):
    invoke, _, _ = demo
    attempt, _ = await invoke("/api/mock-exam/start", {"candidate_code": "ignored"})
    root = f"/api/mock-exam/attempts/{attempt['attempt_id']}"
    for step in exam_router.EXAM_FLOW:
        if step == "rejection_eval":
            generated, _ = await invoke(root + "/steps/rejection_eval/generate", {"prompt": "지시"})
            assert all(set(item) == {"id", "text"} for item in generated["items"])
        if step == "dev_prompting":
            run, _ = await invoke(
                root + "/dev-run", {"prompt": _STEP_INPUT["dev_prompting"]["prompts"][0], "turn": 1}
            )
            _assert_no_scores(run)
        result, _ = await invoke(root + f"/steps/{step}/submit", _STEP_INPUT[step])
        _assert_no_scores(result)
        assert result["recorded"]
    repeated, _ = await invoke(root + "/steps/context_engineering/retry")
    _assert_no_scores(repeated)
    finished, _ = await invoke(root + "/finish")
    assert finished == {"completed": True}
    state = (await client.get(root)).json()
    assert state["status"] == "completed" and state["current_step"] is None


async def test_development_bulk_evaluation_remains_a_real_multi_turn_flow(
    client, demo, monkeypatch
):
    from feature_dev_prompting import api, evaluator
    from feature_dev_prompting.models import CaseResult

    class Solver:
        def complete(self, *args, **kwargs):
            return "def solution(): return 1"

    monkeypatch.setattr(
        api,
        "evaluate",
        lambda *args, **kwargs: evaluator.evaluate(
            *args,
            **kwargs,
            runner=lambda *a, **k: [
                CaseResult(index=0, hidden=False, passed=True, status="pass", expected="1", got="1")
            ],
        ),
    )
    app.dependency_overrides[api.get_solver_client] = lambda: Solver()
    result, _ = await demo[0](
        "/dev-prompting/evaluate",
        {
            "problem_id": "stepping-stones",
            "prompts": ["지시", "추가 지시"],
        },
    )
    assert result["solved"] and len(result["turns"]) == 1
