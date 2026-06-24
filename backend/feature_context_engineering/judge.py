"""LLM-as-judge: does the candidate CLAUDE.md cover the project's ground-truth checklist?

Pipeline (SPEC §5): for each Criterion the judge returns covered + a verbatim quote from the
candidate doc. A deterministic guard then REJECTS any "covered" whose quote isn't actually in
the submission (extractive grounding → kills judge hallucination/leniency). Score = weighted
coverage. The LLM is mocked in unit tests via the LLMClient seam.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor

from app.judge.consensus import tally
from feature_context_engineering.models import (
    ComponentScore,
    Criterion,
    CriterionResult,
    CriterionVerdict,
    DimensionScore,
    Project,
    Submission,
)
from feature_context_engineering.rubric import get_rubric
from llm.client import LLMClient

COVERAGE_WEIGHT = 0.40

SYSTEM_PROMPT = (
    "You are a strict, literal evaluator of a project's CLAUDE.md (an agent-context file). "
    "You are given the project, the candidate's CLAUDE.md, and a checklist of facts a good "
    "CLAUDE.md for THIS project must convey. For each checklist item decide whether the "
    "candidate's CLAUDE.md conveys it — judge meaning, not wording. CRITICAL: when covered is "
    "true you MUST copy a short VERBATIM quote from the candidate's CLAUDE.md as evidence; if "
    "you cannot quote it, it is NOT covered. Do not credit facts that are merely true of the "
    "project but absent from the document. Output ONLY a JSON array, one object per checklist "
    'id: {"id": str, "covered": bool, "evidence": str, "reason": str}.'
)


def _tree(project: Project) -> str:
    return "\n".join(f.path for f in project.files)


def build_prompt(project: Project, submission: Submission, criteria: list[Criterion]) -> str:
    """Compose the judge's user message."""

    checklist = "\n".join(f"- {c.id}: {c.text}" for c in criteria)
    return (
        f"# 프로젝트\n{project.title}\n{project.brief}\n\n"
        f"# 파일 트리\n{_tree(project)}\n\n"
        f"# 후보 CLAUDE.md\n{submission.claude_md}\n\n"
        f"# 체크리스트 (각 항목이 위 CLAUDE.md에 포함됐는지 판정)\n{checklist}\n\n"
        "# 출력\n위 id마다 한 객체씩, JSON 배열만 출력."
    )


def _normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def _extract_json_array(raw: str) -> list:
    """Pull the JSON array out of the model output; tolerant of fences/prose."""

    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def parse_verdicts(
    raw: str, criteria: list[Criterion], submission: Submission
) -> list[CriterionVerdict]:
    """Parse model output into one verdict per criterion, enforcing extractive grounding.

    Any criterion missing from the output is treated as not covered. Any "covered" whose
    evidence quote is not actually present in the submission is downgraded to not covered.
    """

    by_id = {}
    for item in _extract_json_array(raw):
        if isinstance(item, dict) and "id" in item:
            by_id[str(item["id"])] = item

    doc = _normalize(submission.claude_md)
    verdicts: list[CriterionVerdict] = []
    for crit in criteria:
        item = by_id.get(crit.id)
        if not item:
            verdicts.append(CriterionVerdict(id=crit.id, covered=False, reason="missing"))
            continue
        covered = bool(item.get("covered"))
        evidence = str(item.get("evidence") or "")
        reason = str(item.get("reason") or "")
        if covered:
            grounded = bool(evidence.strip()) and _normalize(evidence) in doc
            if not grounded:
                covered = False
                reason = (reason + " · 인용 근거가 문서에 없음").strip(" ·")
        verdicts.append(
            CriterionVerdict(id=crit.id, covered=covered, evidence=evidence, reason=reason)
        )
    return verdicts


def coverage_score(verdicts: list[CriterionVerdict], criteria: list[Criterion]) -> float:
    """Weighted coverage as a 0–100 percentage."""

    total = sum(c.weight for c in criteria)
    if total <= 0:
        return 0.0
    weight = {c.id: c.weight for c in criteria}
    got = sum(weight.get(v.id, 0.0) for v in verdicts if v.covered)
    return round(got / total * 100, 1)


def judge_submission(
    client: LLMClient,
    project: Project,
    submission: Submission,
    criteria: list[Criterion] | None = None,
) -> list[CriterionVerdict]:
    """Run the LLM judge and return grounded per-criterion verdicts."""

    criteria = criteria if criteria is not None else get_rubric(project.id)
    raw = client.complete(SYSTEM_PROMPT, build_prompt(project, submission, criteria))
    return parse_verdicts(raw, criteria, submission)


def coverage_dimension(
    client: LLMClient,
    project: Project,
    submission: Submission,
    criteria: list[Criterion] | None = None,
) -> tuple[DimensionScore, list[CriterionResult]]:
    """Coverage axis: judge each criterion and return (dimension score, per-criterion results)."""

    criteria = criteria if criteria is not None else get_rubric(project.id)
    verdicts = {v.id: v for v in judge_submission(client, project, submission, criteria)}
    results = [
        CriterionResult(
            id=c.id,
            text=c.text,
            category=c.category,
            covered=verdicts[c.id].covered if c.id in verdicts else False,
            evidence=verdicts[c.id].evidence if c.id in verdicts else "",
        )
        for c in criteria
    ]
    covered = sum(1 for r in results if r.covered)
    dim = DimensionScore(
        key="coverage",
        label="컨벤션·모호성 커버리지",
        score=coverage_score(list(verdicts.values()), criteria),
        weight=COVERAGE_WEIGHT,
        detail=f"{covered}/{len(criteria)} 충족",
    )
    return dim, results


DEFAULT_COVERAGE_RUNS = 3


def coverage_consensus(
    client: LLMClient,
    project: Project,
    submission: Submission,
    criteria: list[Criterion] | None = None,
    runs: int = DEFAULT_COVERAGE_RUNS,
) -> tuple[DimensionScore, list[CriterionResult]]:
    """Coverage axis with consensus: judge ``runs`` times and majority-vote each criterion.

    Per-criterion ``agreement`` (share of runs backing the majority verdict) is surfaced as a
    confidence signal — a low value flags a criterion the judge keeps flip-flopping on. The
    dimension score is computed on the majority verdicts; ``runs=1`` reduces to a single call.
    """

    criteria = criteria if criteria is not None else get_rubric(project.id)
    runs = max(1, runs)
    # The runs are independent samples of the same judge — run them concurrently instead of
    # sequentially. The OpenAI client is a blocking call, so a thread pool overlaps the
    # network waits (3 sequential calls -> ~1 call of wall-clock). Order is irrelevant since
    # each result is keyed by criterion id below.
    def _one(_: int) -> dict[str, CriterionVerdict]:
        return {v.id: v for v in judge_submission(client, project, submission, criteria)}

    if runs == 1:
        samples = [_one(0)]
    else:
        with ThreadPoolExecutor(max_workers=runs) as pool:
            samples = list(pool.map(_one, range(runs)))

    majority: list[CriterionVerdict] = []
    results: list[CriterionResult] = []
    agreements: list[float] = []
    for c in criteria:
        votes = [(s[c.id].covered if c.id in s else False) for s in samples]
        decision = tally(votes)
        covered = bool(decision.winner)
        agreements.append(decision.agreement)
        evidence = next(
            (s[c.id].evidence for s in samples if c.id in s and s[c.id].covered == covered),
            "",
        )
        majority.append(CriterionVerdict(id=c.id, covered=covered, evidence=evidence))
        results.append(
            CriterionResult(
                id=c.id,
                text=c.text,
                category=c.category,
                covered=covered,
                evidence=evidence,
                agreement=round(decision.agreement, 4),
            )
        )

    covered_n = sum(1 for r in results if r.covered)
    mean_agreement = round(sum(agreements) / len(agreements), 4) if agreements else 1.0
    dim = DimensionScore(
        key="coverage",
        label="컨벤션·모호성 커버리지",
        score=coverage_score(majority, criteria),
        weight=COVERAGE_WEIGHT,
        detail=f"{covered_n}/{len(criteria)} 충족 · {runs}회 합의 {round(mean_agreement * 100)}%",
    )
    return dim, results


class ChecklistJudgeScorer:
    """ContextScorer that scores ground-truth coverage via the LLM judge."""

    name = "context-coverage"

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def score(self, submission: Submission, project: Project) -> ComponentScore:
        criteria = get_rubric(project.id)
        if not criteria:
            return ComponentScore(name=self.name, score=0.0, detail="no rubric for project")
        verdicts = judge_submission(self._client, project, submission, criteria)
        score = coverage_score(verdicts, criteria)
        covered = sum(1 for v in verdicts if v.covered)
        missed = [v.id for v in verdicts if not v.covered]
        detail = f"{covered}/{len(criteria)} criteria covered"
        if missed:
            detail += f"; missing: {', '.join(missed)}"
        return ComponentScore(name=self.name, score=score, detail=detail)


_PAIRWISE_SYSTEM = (
    "두 개의 CLAUDE.md(에이전트 컨텍스트 파일)가 같은 프로젝트에 대해 작성되었습니다. 프로젝트, "
    "파일 트리, 그리고 후보 A와 B가 주어집니다. 어느 쪽이 코딩 에이전트를 더 잘 안내하는지 "
    "고르세요 — 프로젝트의 필수 명령·구조·컨벤션·경계를 더 정확하고 군더더기 없이 담은 쪽. "
    "길이나 서식이 아니라 에이전트에게의 유용성으로 판단하고, 어느 쪽이 먼저 제시됐는지는 "
    '무시하세요(내용만). JSON만 출력: {"winner": "A" | "B" | "tie", "reason": str}.'
)


def build_pairwise_prompt(project: Project, sub_a: Submission, sub_b: Submission) -> str:
    """Compose the pairwise judge's user message (content-only, order-agnostic)."""

    return (
        f"# 프로젝트\n{project.title}\n{project.brief}\n\n# 파일 트리\n{_tree(project)}\n\n"
        f"# 후보 A\n{sub_a.claude_md}\n\n# 후보 B\n{sub_b.claude_md}\n\n# 출력\nJSON만."
    )


def _parse_winner(raw: str) -> str:
    """Pull {"winner": ...} out of the model output; default to 'tie' on anything unclear."""

    obj: dict = {}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            obj = parsed
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    obj = parsed
            except json.JSONDecodeError:
                obj = {}
    winner = str(obj.get("winner", "")).strip().upper()
    return winner if winner in ("A", "B") else "tie"


def judge_pairwise(
    client: LLMClient, project: Project, sub_a: Submission, sub_b: Submission
) -> str:
    """Ask which of two CLAUDE.md docs orients an agent better. Returns 'A' | 'B' | 'tie'.

    Runs COLD (temperature 0.0) — a judge must be reproducible. Position bias is measured by
    the harness re-running this with A/B swapped and checking whether the verdict flips.
    """

    raw = client.complete(
        _PAIRWISE_SYSTEM,
        build_pairwise_prompt(project, sub_a, sub_b),
        temperature=0.0,
    )
    return _parse_winner(raw)
