"""One-time generator for the harness's synthetic candidate submissions.

Hits a REAL LLM (needs OPENAI_API_KEY). For each problem and each author model
in the panel, it generates candidate flaw lists at three quality levels
(strong / mediocre / hallucinated) and writes ``synthetic_submissions.json``.

The output is committed as a fixture so the harness and its tests don't need a
key. Re-run only when you want to refresh the synthetic set; then re-label the
new submissions in ``human_gold.json``.

    python -m app.features.test_design.scripts.gen_synthetic
"""

import asyncio
import json
from pathlib import Path

from pydantic import BaseModel

from app.features.test_design.problems import PROBLEMS
from app.llm.structured import complete_structured

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

_QUALITY_PROMPTS = {
    "strong": "추가로 검증해야 할 항목을 근본 원인·조건까지 정확하고 폭넓게 3~4개 짚으세요.",
    "mediocre": (
        "추가 검증 항목을 1~2개만, 다소 모호하게(증상 위주로) 짚으세요. "
        "이미 구현된 기본 테스트를 그대로 다시 적은 항목을 하나 섞어도 됩니다."
    ),
    "hallucinated": "실제 검증 항목과 무관하거나 사실이 틀린 지적을 1~2개 적으세요.",
}


class _Submission(BaseModel):
    flaws: list[str]


async def _generate() -> list[dict]:
    panel = json.loads((_FIXTURES / "panel_models.json").read_text(encoding="utf-8"))
    out: list[dict] = []
    counter = 0
    for pi, problem in enumerate(PROBLEMS):
        for author in panel["author_models"]:
            for quality, directive in _QUALITY_PROMPTS.items():
                counter += 1
                system = (
                    "당신은 테스트 설계 평가 응시자입니다. 주어진 기능 시나리오를 보고 검증해야 할 "
                    f"항목을 한국어 자연어 항목 리스트로 작성하세요. {directive}"
                )
                user = json.dumps({"spec": problem.spec}, ensure_ascii=False)
                sub = await complete_structured(system, user, _Submission, model=author)
                out.append(
                    {
                        "key": f"s{counter}",
                        "problem_index": pi,
                        "author_model": author,
                        "quality": quality,
                        "flaws": sub.flaws,
                    }
                )
    return out


def main() -> None:
    submissions = asyncio.run(_generate())
    path = _FIXTURES / "synthetic_submissions.json"
    path.write_text(json.dumps(submissions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(submissions)} submissions to {path}")
    print(
        "Now hand-label these in human_gold.json (same keys): for each key set "
        "matched_ids to the practical-scenario flaw ids it covers (a restated "
        "provided_test is neutral — leave it out) and recall = len(matched_ids)/"
        "len(problem flaws). Then run `pytest -m harness` to check coherence."
    )


if __name__ == "__main__":
    main()
