"""Coverage consensus: majority-vote each criterion across N judge runs, surface agreement."""

import json

import pytest

from feature_context_engineering.judge import coverage_consensus
from feature_context_engineering.models import Criterion, FileNode, Project, Submission

CRITERIA = [Criterion(id="a", text="A"), Criterion(id="b", text="B")]
PROJECT = Project(id="x", title="X", brief="b", files=[FileNode(path="app/main.py", content="x")])
SUB = Submission(project_id="x", claude_md="doc covering A and B here")


class SeqClient:
    """Returns canned judge responses in order across successive calls."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.i = 0

    def complete(self, system, user):
        r = self.responses[self.i % len(self.responses)]
        self.i += 1
        return r


def _resp(covered):
    return json.dumps(
        [
            {"id": i, "covered": i in covered, "evidence": "A and B" if i in covered else ""}
            for i in ("a", "b")
        ]
    )


def test_consensus_majority_vote_and_agreement():
    # b flips covered/not/covered across 3 runs -> majority covered at 2/3 agreement; a is stable.
    client = SeqClient([_resp({"a", "b"}), _resp({"a"}), _resp({"a", "b"})])
    _dim, results = coverage_consensus(client, PROJECT, SUB, CRITERIA, runs=3)
    by = {r.id: r for r in results}
    assert by["a"].covered is True
    assert by["a"].agreement == pytest.approx(1.0)
    assert by["b"].covered is True
    assert by["b"].agreement == pytest.approx(2 / 3, abs=1e-3)  # stored rounded to 4dp


def test_consensus_minority_verdict_loses():
    # b covered in only 1 of 3 runs -> a single noisy roll can't make it covered.
    client = SeqClient([_resp({"a", "b"}), _resp({"a"}), _resp({"a"})])
    _dim, results = coverage_consensus(client, PROJECT, SUB, CRITERIA, runs=3)
    by = {r.id: r for r in results}
    assert by["b"].covered is False
    assert by["b"].agreement == pytest.approx(2 / 3, abs=1e-3)  # two runs agree on "not covered"


def test_consensus_single_run_is_full_agreement():
    client = SeqClient([_resp({"a"})])
    dim, results = coverage_consensus(client, PROJECT, SUB, CRITERIA, runs=1)
    by = {r.id: r for r in results}
    assert by["a"].agreement == pytest.approx(1.0)
    assert by["b"].covered is False
    assert "1회 합의" in dim.detail
