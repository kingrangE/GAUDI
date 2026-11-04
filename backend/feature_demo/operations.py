"""Allowlisted adapters retain native validation, response filtering, and ownership rules."""

import re
from dataclasses import dataclass

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, create_model
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.coding_test import schemas as coding
from app.features.cs_eval import schemas as cs
from app.features.mock_exam import exam_router as exam
from app.features.office_prompting import schemas as office
from app.features.rejection_eval import schemas as rejection
from app.features.test_design import schemas as tests
from feature_context_engineering.models import Submission
from feature_demo.models import DemoResource
from feature_dev_prompting import api as dev
from feature_spec_design.api import EvaluateRequest as SpecInput


class Empty(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NativeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: dict = Field(default_factory=dict)
    body: dict = Field(default_factory=dict)


@dataclass(frozen=True)
class Operation:
    feature: str
    action: str
    path: str
    body_model: type[BaseModel]

    def validate(self, data: dict) -> NativeInput:
        value = NativeInput.model_validate(data)
        fields = {
            key: (
                (int, Field(ge=0))
                if key.endswith("_index")
                else (str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$"))
            )
            for key in re.findall(r"{(\w+)}", self.path)
        }
        params = create_model(
            "OperationParams", __config__=ConfigDict(extra="forbid"), **fields
        ).model_validate(value.params)
        return NativeInput(
            params=params.model_dump(),
            body=self.body_model.model_validate(value.body).model_dump(mode="json"),
        )


OPERATIONS = [
    Operation(
        "context_engineering", "post_submission", "/api/context-engineering/submissions", Submission
    ),
    Operation("spec_design", "evaluate", "/spec-design/evaluate", SpecInput),
    Operation("dev_prompting", "evaluate", "/dev-prompting/evaluate", dev.EvaluateRequest),
    Operation("dev_prompting", "create_run", "/dev-prompting/runs", dev.CreateRunRequest),
    Operation("dev_prompting", "next_turn", "/dev-prompting/runs/{run_id}/turns", dev.TurnRequest),
    Operation(
        "coding_test", "run", "/api/coding-test/problems/{problem_id}/run", coding.RunRequest
    ),
    Operation(
        "coding_test",
        "create_submission",
        "/api/coding-test/submissions",
        coding.CreateSubmissionRequest,
    ),
    Operation("cs_eval", "create_session", "/api/cs-eval/sessions", cs.CreateSessionRequest),
    Operation("test_design", "create_session", "/test-design/sessions", tests.CreateSessionRequest),
    Operation(
        "test_design",
        "submit",
        "/test-design/sessions/{session_id}/problems/{problem_index}/submit",
        tests.SubmitRequest,
    ),
    Operation(
        "rejection_eval",
        "create_session",
        "/api/rejection-eval/sessions",
        rejection.CreateSessionRequest,
    ),
    Operation(
        "rejection_eval",
        "generate",
        "/api/rejection-eval/sessions/{session_id}/topics/{topic_index}/generate",
        rejection.GenerateRequest,
    ),
    Operation(
        "rejection_eval",
        "submit",
        "/api/rejection-eval/sessions/{session_id}/topics/{topic_index}/submit",
        rejection.SubmitRequest,
    ),
    Operation("rejection_eval", "score", "/api/rejection-eval/sessions/{session_id}/score", Empty),
    Operation(
        "office_prompting",
        "create_session",
        "/api/office-prompting/sessions",
        office.CreateSessionRequest,
    ),
    Operation(
        "office_prompting",
        "run",
        "/api/office-prompting/sessions/{session_id}/problems/{problem_index}/run",
        office.RunRequest,
    ),
    Operation(
        "office_prompting", "score", "/api/office-prompting/sessions/{session_id}/score", Empty
    ),
    Operation("mock_exam", "start", "/api/mock-exam/start", exam.StartRequest),
    Operation(
        "mock_exam",
        "generate_rejection_items",
        "/api/mock-exam/attempts/{attempt_id}/steps/rejection_eval/generate",
        exam.GenerateRequest,
    ),
    Operation(
        "mock_exam", "run_dev_turn", "/api/mock-exam/attempts/{attempt_id}/dev-run", dev.TurnRequest
    ),
    Operation(
        "mock_exam",
        "submit_step",
        "/api/mock-exam/attempts/{attempt_id}/steps/{feature_key}/submit",
        exam.StepSubmitRequest,
    ),
    Operation(
        "mock_exam",
        "retry_step",
        "/api/mock-exam/attempts/{attempt_id}/steps/{feature_key}/retry",
        Empty,
    ),
    Operation("mock_exam", "finish", "/api/mock-exam/attempts/{attempt_id}/finish", Empty),
]


def operation_for(feature: str, action: str) -> Operation:
    for operation in OPERATIONS:
        if (operation.feature, operation.action) == (feature, action):
            return operation
    raise ValueError("unsupported evaluation operation")


async def check_owner(
    db: AsyncSession,
    owner_id: str,
    operation: Operation,
    data: NativeInput,
    *,
    check_state: bool = True,
):
    for key in ("session_id", "run_id", "attempt_id"):
        if key in data.params:
            owner = await db.get(DemoResource, (operation.feature, data.params[key]))
            if owner is None or owner.session_id != owner_id:
                raise HTTPException(status_code=404, detail="resource not found")
    if check_state and operation.feature == "mock_exam" and "attempt_id" in data.params:
        attempt = await exam._get_attempt_or_404(db, data.params["attempt_id"])
        if operation.action == "finish" and attempt.status == "completed":
            return
        check_time = operation.action in {"generate_rejection_items", "run_dev_turn"}
        if operation.action == "submit_step" and data.params.get("feature_key") != "dev_prompting":
            from sqlalchemy import select

            saved = await db.scalar(
                select(exam.ExamSubmission.id).where(
                    exam.ExamSubmission.exam_attempt_id == attempt.id,
                    exam.ExamSubmission.feature_key == data.params.get("feature_key"),
                )
            )
            check_time = saved is None
        exam._require_open(attempt, check_time=check_time)
