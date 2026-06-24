"""LLM generation: turn the candidate's prompt into a design.

The model designs **only from the candidate's prompt** — it is never given the
topic's functional-requirements spec. It faithfully follows what the candidate
asked for and additionally injects 0..N intentional wrong designs
(`is_flawed`/`flaw_type`). Whether each item is in the requirements is decided
later by the judge. Unit tests mock this function.
"""

from app.features.rejection_eval.schemas import GenerationOutput
from app.llm.structured import complete_structured

_SYSTEM = """\
당신은 소프트웨어 설계를 생성하는 AI입니다. 주어진 주제와 사용자(응시자)의 프롬프트에 따라
구현을 위한 '기술 선택 결정' 항목 12~16개를 제시하세요. 각 항목은 '우리는 이런 기술/방식을
선택하기로 했다' 형태의 한 문장 결정입니다.

- **최대한 응시자 프롬프트에 충실하게** 설계하세요. 별도의 요구사항 명세는 주어지지 않습니다.
  프롬프트가 모호하거나 빠진 부분은 합리적으로 결정하되, 임의로 범위를 넓히지 마세요.

평가용으로, 이 항목들 중 3~5개에 **의도적인 결함**을 심으세요. 결함은 두 종류입니다:
- wrong_tech: 기술을 잘못 적용함
  (예: 비밀번호를 단순 SHA-256으로 저장, 페이지네이션 없는 풀 테이블 스캔, PII 평문 응답 포함)
- wrong_direction: 개발 방향성이 잘못됨
  (예: 실시간 알림에 폴링만 사용, refund 이벤트를 긍정 신호로 오분류, late-arriving 이벤트 무시)

규칙:
- 결함 개수는 3~5개로 정하세요.
- 각 항목에 고유한 id(예: "item-1"), 결정 문장 text, is_flawed(bool),
  flaw_type(결함이 없으면 "none"), explanation(왜 옳은지/틀렸는지 한국어 1문장)을 채우세요.
- 결함 항목도 표면적으로 그럴듯하게 작성해 쉽게 들키지 않도록 하세요.
"""


async def generate_design(topic_title: str, prompt: str) -> GenerationOutput:
    user = f"주제: {topic_title}\n\n응시자 프롬프트:\n{prompt}"
    return await complete_structured(_SYSTEM, user, GenerationOutput)
