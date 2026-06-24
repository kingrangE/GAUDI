"""LLM judging: semantically match a candidate's verification items to the answer set.

The candidate reads a prose scenario (a real-world feature) and lists what must
be verified about it. The judge sees the hidden answer set (it runs server-side)
and decides, for each ground-truth verification item, whether any of the
candidate's natural-language items refers to it — plus a 0-2 quality score and
which submissions are off-target. All numeric scoring (recall/precision/weighted)
is then computed deterministically in ``scoring.py``; the judge only produces the
matching + a short report.

Unit tests mock this function.
"""

import json

from app.features.test_design.problems import Problem
from app.features.test_design.schemas import JudgeOutput, PairwiseVerdict
from app.llm.structured import complete_structured

_SYSTEM = """\
당신은 '테스트 설계 평가'의 채점관입니다. 어떤 기능의 구현 시나리오와, 그 구현에 대해 **이미
구현되어 제공된 기본 테스트 목록**, 그리고 그 위에 **추가로 반드시 검증해야 할 항목 목록**
(엣지케이스·실패 모드 등, 각 항목의 id와 설명)이 주어집니다. 응시자는 제공된 기본 테스트 외에
추가로 필요한 검증 항목을 자연어로 작성했고, 그 **검증 항목 목록**(0부터 시작하는 인덱스)이
함께 주어집니다.

각 정답(추가) 검증 항목마다 다음을 판정하세요:
- matched: 응시자의 서술 중 그 항목을 가리키는 것이 있으면 true, 없으면 false.
- candidate_index: 매칭된 응시자 서술의 인덱스(매칭이 없으면 null).
- quality: 매칭됐을 때 서술의 품질 0~2 (0=증상만 언급하거나 모호함, 1=핵심을 맞게 짚음,
  2=근본 원인과 발생 조건까지 정확히 명시). 매칭이 없으면 0.

규칙:
- 표현이 달라도 의미가 같으면 매칭하세요(의미 기반 매칭).
- 하나의 응시자 서술이 여러 정답 항목에 해당하면 가장 잘 맞는 항목에 매칭하세요.
- 응시자 서술이 **제공된 기본 테스트를 단순히 다시 적은 것**이면(이미 구현된 것) 매칭도 false
  positive도 아닙니다. 그 인덱스는 already_covered_indices에 담으세요(중립).
- 정답 항목과 무관하거나 틀린(허위) 응시자 서술의 인덱스는 false_positive_indices에 담으세요.
- report: 응시자의 검증 설계 능력을 1~2줄 한국어로 요약하세요(무엇을 잘 짚고 무엇을 놓쳤는지).
"""


async def judge_submission(
    problem: Problem, candidate_flaws: list[str], model: str | None = None
) -> JudgeOutput:
    payload = {
        "title": problem.title,
        "spec": problem.spec,
        "provided_tests": list(problem.provided_tests),
        "ground_truth": [{"id": f.id, "text": f.text} for f in problem.flaws],
        "candidate_flaws": list(candidate_flaws),
    }
    user = json.dumps(payload, ensure_ascii=False)
    return await complete_structured(_SYSTEM, user, JudgeOutput, model=model)


_PAIRWISE_SYSTEM = """\
당신은 '테스트 설계 평가'의 채점관입니다. 동일한 기능 시나리오에 대해 두 응시자(A, B)가 작성한
'검증 항목' 목록과 정답 검증 항목 목록이 주어집니다. 더 우수한(정답 항목을 더 정확하고 폭넓게
짚은) 쪽을 고르세요. 우열을 가리기 어려우면 "tie". 순서가 아니라 내용만으로 판단하세요.
"""


async def judge_pairwise(
    problem: Problem,
    flaws_a: list[str],
    flaws_b: list[str],
    model: str | None = None,
) -> PairwiseVerdict:
    payload = {
        "title": problem.title,
        "spec": problem.spec,
        "provided_tests": list(problem.provided_tests),
        "ground_truth": [{"id": f.id, "text": f.text} for f in problem.flaws],
        "submission_A": list(flaws_a),
        "submission_B": list(flaws_b),
    }
    user = json.dumps(payload, ensure_ascii=False)
    return await complete_structured(_PAIRWISE_SYSTEM, user, PairwiseVerdict, model=model)
