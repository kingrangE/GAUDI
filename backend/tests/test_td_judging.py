"""The judge wrapper builds the right payload and returns structured output.

The actual LLM call (`complete_structured`) is mocked — we only verify the
wiring: ground truth + candidate flaws go in, a JudgeOutput comes back.
"""

import json

from app.features.test_design import judging
from app.features.test_design.problems import PROBLEMS
from app.features.test_design.schemas import JudgeMatch, JudgeOutput


async def test_judge_submission_builds_payload_and_returns_output(monkeypatch):
    captured = {}

    async def fake_complete(system, user, schema, model=None):
        captured["system"] = system
        captured["user"] = user
        captured["schema"] = schema
        captured["model"] = model
        return JudgeOutput(
            matches=[JudgeMatch(ground_truth_id="f1", matched=True, candidate_index=0, quality=2)],
            false_positive_indices=[],
            report="ok",
        )

    monkeypatch.setattr(judging, "complete_structured", fake_complete)

    problem = PROBLEMS[0]
    out = await judging.judge_submission(problem, ["파일 크기 상한이 없다"])

    assert isinstance(out, JudgeOutput)
    assert out.matches[0].ground_truth_id == "f1"
    assert captured["schema"] is JudgeOutput
    payload = json.loads(captured["user"])
    # ground truth item ids are passed to the judge
    assert {g["id"] for g in payload["ground_truth"]} == {f.id for f in problem.flaws}
    assert payload["candidate_flaws"] == ["파일 크기 상한이 없다"]
    # scenarios are prose-only — no code is sent to the judge
    assert payload["spec"]
    assert "code" not in payload
    # provided basic tests are given to the judge as context
    assert payload["provided_tests"] == list(problem.provided_tests)
