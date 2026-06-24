"""Fixed, human-authored CS 서술형 questions (seed data).

Each question carries the candidate-facing prompt plus judge-only grounding:
a reference answer and a rubric (`key_points` the answer should hit,
`common_pitfalls` to watch for). `seed_cs_questions.py` loads these into the DB.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionSeed:
    id: str
    domain: str
    prompt_md: str
    reference_answer: str
    rubric: dict
    ordinal: int


_DS_HASHMAP = QuestionSeed(
    id="ds-hashmap",
    domain="자료구조",
    prompt_md=(
        "해시 테이블이 평균 **O(1)** 조회를 제공하는 원리를 설명하고, **최악의 경우 "
        "O(n)** 으로 악화되는 상황과 이를 완화하는 기법을 함께 서술하세요."
    ),
    reference_answer=(
        "해시 함수가 키를 버킷 인덱스로 매핑해 평균적으로 상수 시간에 접근한다. "
        "서로 다른 키가 같은 버킷에 들어가는 충돌이 발생하면 체이닝(연결 리스트)이나 "
        "개방 주소법으로 해결한다. 로드 팩터가 커지면 충돌이 늘어 성능이 나빠지므로 "
        "임계치를 넘으면 더 큰 테이블로 리해싱한다. 모든 키가 한 버킷에 몰리는 최악의 "
        "경우 조회가 O(n)이 되며, 좋은 해시 함수와 리사이징으로 이를 완화한다."
    ),
    rubric={
        "key_points": [
            "해시 함수로 버킷 인덱스 계산",
            "충돌",
            "체이닝",
            "개방 주소법",
            "로드 팩터와 리해싱",
        ],
        "common_pitfalls": [
            "충돌을 아예 언급하지 않음",
            "최악의 경우 O(n)을 모름",
            "리해싱/리사이징 누락",
        ],
    },
    ordinal=0,
)

_OS_PROCESS_THREAD = QuestionSeed(
    id="os-process-thread",
    domain="OS",
    prompt_md=(
        "**프로세스와 스레드의 차이**를 메모리 관점에서 설명하고, 둘 사이의 **컨텍스트 "
        "스위칭 비용** 차이가 왜 발생하는지 서술하세요."
    ),
    reference_answer=(
        "프로세스는 독립된 주소 공간을 가지며, 한 프로세스의 스레드들은 그 주소 공간을 "
        "공유한다. 따라서 스레드 간 전환은 주소 공간을 바꾸지 않아 상대적으로 가볍고, "
        "프로세스 전환은 가상 메모리 매핑이 바뀌어 TLB·캐시가 무효화되므로 비용이 크다. "
        "스레드는 스택과 레지스터 정도만 교체하면 되므로 컨텍스트 스위칭이 더 저렴하다."
    ),
    rubric={
        "key_points": [
            "프로세스는 독립 주소 공간",
            "스레드는 주소 공간 공유",
            "컨텍스트 스위칭",
            "TLB",
            "스레드가 더 가벼움",
        ],
        "common_pitfalls": [
            "주소 공간 공유 여부를 뒤바꿈",
            "전환 비용 차이의 이유를 설명 못함",
        ],
    },
    ordinal=1,
)

_NET_TCP = QuestionSeed(
    id="net-tcp-handshake",
    domain="네트워크",
    prompt_md=(
        "**TCP 3-way handshake** 과정을 단계별로 설명하고, TCP가 **신뢰성**을 보장하는 "
        "방법(순서 보장·손실 복구 등)을 서술하세요."
    ),
    reference_answer=(
        "클라이언트가 SYN을 보내고, 서버가 SYN-ACK로 응답하며, 클라이언트가 ACK를 "
        "보내 연결을 수립한다(3-way handshake). 각 세그먼트에는 시퀀스 번호가 있어 "
        "수신 측이 순서를 복원하고, ACK 확인 응답으로 수신을 알린다. 일정 시간 ACK가 "
        "오지 않으면 재전송하며, 흐름 제어와 혼잡 제어로 전송 속도를 조절해 신뢰성을 "
        "확보한다."
    ),
    rubric={
        "key_points": [
            "SYN",
            "SYN-ACK",
            "ACK",
            "시퀀스 번호",
            "재전송",
            "흐름 제어와 혼잡 제어",
        ],
        "common_pitfalls": [
            "핸드셰이크 단계 순서를 틀림",
            "신뢰성 보장 메커니즘을 빠뜨림",
            "UDP와 혼동",
        ],
    },
    ordinal=2,
)

_DB_INDEX = QuestionSeed(
    id="db-index",
    domain="DB",
    prompt_md=(
        "데이터베이스 **인덱스**가 조회를 빠르게 하는 원리를 설명하고, 인덱스를 "
        "**무분별하게 늘릴 때의 단점**(쓰기 비용 등)을 함께 서술하세요."
    ),
    reference_answer=(
        "인덱스는 보통 B-트리/B+트리 같은 정렬된 자료구조로 키를 보관해, 풀 테이블 "
        "스캔 대신 탐색 범위를 좁혀 조회를 빠르게 한다. 하지만 INSERT·UPDATE·DELETE "
        "마다 인덱스도 함께 갱신해야 하므로 쓰기 비용과 저장 공간이 늘어난다. 따라서 "
        "조회 패턴에 맞춰 꼭 필요한 인덱스만 두는 것이 좋다."
    ),
    rubric={
        "key_points": [
            "B-트리",
            "정렬된 자료구조로 탐색 범위 축소",
            "풀 스캔 회피",
            "쓰기 시 인덱스 갱신 비용",
            "저장 공간 증가",
        ],
        "common_pitfalls": [
            "쓰기 비용 단점을 언급 안 함",
            "인덱스를 무조건 많을수록 좋다고 답함",
        ],
    },
    ordinal=3,
)


QUESTIONS: tuple[QuestionSeed, ...] = (
    _DS_HASHMAP,
    _OS_PROCESS_THREAD,
    _NET_TCP,
    _DB_INDEX,
)
