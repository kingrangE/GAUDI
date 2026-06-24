"""LLM generation: turn the candidate's prompt into a flawed design.

The model designs what the candidate asked for, but deliberately injects 0..N
flawed decisions and labels each item with ground truth (`is_flawed`,
`flaw_type`, `explanation`). Unit tests mock this function.
"""

from app.features.rejection_eval.schemas import GenerationOutput
from app.llm.structured import complete_structured

_SYSTEM = """\
당신은 소프트웨어 설계를 생성하는 AI입니다. 주어진 주제와 사용자(응시자)의 프롬프트에 따라
구현을 위한 '기술 선택 결정' 항목 6~8개를 제시하세요. 각 항목은 '우리는 이런 기술/방식을
선택하기로 했다' 형태의 한 문장 결정입니다.

평가용으로, 이 항목들 중 0~N개에 **의도적인 결함**을 심으세요. 결함은 두 종류입니다:
- wrong_tech: 기술을 잘못 적용함 (예: 비밀번호를 단순 SHA-256으로 저장)
- wrong_direction: 기술이 아니라 개발 방향성이 잘못됨 (예: 실시간 알림에 폴링만 사용)

규칙:
- 결함 개수는 0~N개로 무작위에 가깝게 정하세요(전부 올바를 수도 있음).
- 각 항목에 고유한 id(예: "item-1"), 결정 문장 text, is_flawed(bool),
  flaw_type(결함이 없으면 "none"), explanation(왜 옳은지/틀렸는지 한국어 1문장)을 채우세요.
- 결함 항목도 표면적으로 그럴듯하게 작성해 쉽게 들키지 않도록 하세요.
"""


async def generate_design(topic_title: str, prompt: str) -> GenerationOutput:
    user = f"주제: {topic_title}\n\n응시자 프롬프트:\n{prompt}"
    return await complete_structured(_SYSTEM, user, GenerationOutput)
