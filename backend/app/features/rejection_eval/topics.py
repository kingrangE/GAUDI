"""Fixed, human-authored topics for the rejection-ability evaluation.

The same three topics are presented to every candidate so results are
comparable. A topic is only a seed: the candidate writes a prompt for it, and
the LLM generates a design (with 0..N intentional flaws injected) from that.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    title: str
    description: str


TOPICS: tuple[Topic, ...] = (
    Topic(
        title="로그인 / 회원가입 기능",
        description="사용자 인증(가입·로그인·세션/토큰) 백엔드 기능을 설계하도록 지시하세요.",
    ),
    Topic(
        title="게시글 CRUD + 이미지 업로드 API",
        description="게시글 CRUD와 이미지 업로드를 처리하는 API를 설계하도록 지시하세요.",
    ),
    Topic(
        title="실시간 알림 시스템",
        description="실시간 알림을 전달하는 시스템 아키텍처를 설계하도록 지시하세요.",
    ),
)

TOPIC_COUNT = len(TOPICS)
