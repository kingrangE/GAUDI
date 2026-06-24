"""LLM extraction: run the candidate's prompt against the datasets.

The system prompt is neutral except that it fixes the TARGET entity for the
problem (e.g. "return customer_id values"); it never sees the human-facing
problem description. The candidate's prompt supplies the filtering/joining
criteria. Unit tests monkeypatch this function at the service layer.
"""

from app.features.office_prompting import datasets
from app.features.office_prompting.problems import Problem
from app.features.office_prompting.schemas import ExtractionOutput
from app.llm.structured import complete_structured

_SYSTEM_TEMPLATE = """\
당신은 표 형식 데이터(CSV)에 대한 데이터 추출 도구입니다. 아래에 customers, orders, products
세 개의 표가 주어집니다. 사용자가 제시한 '조건'을 정확히 적용하여(필요하면 표들을 조인하여),
조건을 만족하는 **{target_entity} 값들의 목록만** ids로 반환하세요.

규칙:
- 출력은 반드시 조건을 만족하는 {target_entity} 값들의 집합입니다(중복 없이).
- 데이터에 실제로 존재하는 값만 반환하고, 추측하거나 새로 만들어내지 마세요.
- 설명·문장은 출력하지 말고 ids 목록만 채우세요.
"""


async def extract_ids(problem: Problem, candidate_prompt: str) -> ExtractionOutput:
    system = _SYSTEM_TEMPLATE.format(target_entity=problem.target_entity)
    user = f"{datasets.datasets_csv_bundle()}\n\n## 사용자 조건(프롬프트)\n{candidate_prompt}"
    return await complete_structured(system, user, ExtractionOutput)
