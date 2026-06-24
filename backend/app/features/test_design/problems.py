"""Fixed, human-authored problems for the test-design evaluation.

Each problem describes a **real-world service feature** in prose — what the
service does, which technology implements it, and how it is wired together. The
candidate's job is to enumerate *what must be verified* about that
implementation (edge cases, failure modes, race conditions, validation gaps).

The ``flaws`` tuple is the **hidden ground-truth answer set**: the edge cases /
verification points a strong test designer should raise. Despite the field name
(kept for API/scoring stability) these are *verification items*, not code bugs.
It is never serialized to the candidate — only ``title``, ``difficulty`` and the
prose ``spec`` are shown. The same six problems, grouped into three difficulty
tiers, are given to every candidate so results are comparable.

Authored as version-controlled Python constants (mirrors the rejection_eval
``topics.py`` convention); curate/extend by editing this module.
"""

from dataclasses import dataclass
from typing import Literal

Severity = Literal["low", "medium", "high"]
Difficulty = Literal["easy", "medium", "hard"]
# Practical verification categories (not algorithm-bug categories).
FlawCategory = Literal[
    "boundary",
    "error_handling",
    "concurrency",
    "security",
    "data_integrity",
    "validation",
    "performance",
    "correctness",
]


@dataclass(frozen=True)
class Flaw:
    """One ground-truth verification item (edge case) a candidate should raise."""

    id: str
    text: str
    severity: Severity
    category: FlawCategory


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    difficulty: Difficulty
    spec: str
    flaws: tuple[Flaw, ...]


PROBLEMS: tuple[Problem, ...] = (
    # ----- 쉬움 (easy) -------------------------------------------------------
    Problem(
        id="problem_001",
        title="프로필 이미지 업로드 (S3 presigned URL)",
        difficulty="easy",
        spec=(
            "이미지 공유 서비스의 프로필 사진 업로드 기능이다. 클라이언트가 백엔드에 업로드를 "
            "요청하면 백엔드는 S3 presigned PUT URL(유효시간 5분)을 발급한다. 클라이언트는 그 "
            "URL로 이미지를 S3에 직접 PUT 업로드하고, 완료되면 백엔드에 객체 key를 알려준다. "
            "백엔드는 그 key로 만든 이미지 URL을 사용자 프로필에 저장한다."
        ),
        flaws=(
            Flaw(
                id="f1",
                text=(
                    "presigned URL에 Content-Length-Range 같은 크기 상한 조건이 없으면 "
                    "수 GB짜리 파일을 올려 스토리지·비용을 고갈시킬 수 있다."
                ),
                severity="high",
                category="validation",
            ),
            Flaw(
                id="f2",
                text=(
                    "Content-Type/확장자 검증이 없어 이미지가 아닌 HTML·실행파일을 올릴 수 있고, "
                    "그대로 서빙되면 저장형 XSS·악성파일 배포로 이어진다."
                ),
                severity="high",
                category="security",
            ),
            Flaw(
                id="f3",
                text=(
                    "완료 콜백의 객체 key 소유권을 검증하지 않으면, 클라이언트가 임의 key를 보내 "
                    "남의 객체나 존재하지 않는 객체를 자기 프로필에 연결할 수 있다."
                ),
                severity="high",
                category="security",
            ),
            Flaw(
                id="f4",
                text=(
                    "presigned URL 만료(5분) 경계 — 업로드가 길어져 만료되면 PUT이 실패하므로 "
                    "만료 직전/직후 재발급·재시도 흐름을 검증해야 한다."
                ),
                severity="medium",
                category="boundary",
            ),
            Flaw(
                id="f5",
                text=(
                    "콜백만 믿고 S3에 객체가 실제로 존재하는지(HEAD) 확인하지 않으면, 업로드 "
                    "실패 시에도 깨진 이미지 URL이 프로필에 저장된다."
                ),
                severity="medium",
                category="data_integrity",
            ),
            Flaw(
                id="f6",
                text=(
                    "프로필 사진 교체 시 이전 S3 객체를 정리하지 않으면 "
                    "orphan 객체가 계속 쌓인다."
                ),
                severity="low",
                category="data_integrity",
            ),
        ),
    ),
    Problem(
        id="problem_002",
        title="회원가입 이메일 중복 체크",
        difficulty="easy",
        spec=(
            "회원가입 REST API다. 클라이언트가 이메일/비밀번호를 POST하면, 서버는 users 테이블에서 "
            "같은 이메일이 있는지 SELECT로 조회하고 없으면 INSERT한다. 이메일 컬럼에는 DB unique "
            "인덱스가 걸려 있다."
        ),
        flaws=(
            Flaw(
                id="f1",
                text=(
                    "이메일을 정규화(소문자화·trim)하지 않으면 'A@x.com'과 'a@x.com'이 서로 다른 "
                    "값으로 취급돼 같은 사람이 중복 가입된다."
                ),
                severity="high",
                category="data_integrity",
            ),
            Flaw(
                id="f2",
                text=(
                    "SELECT-후-INSERT 사이에 동일 이메일 동시 요청이 들어오면 둘 다 중복 검사를 "
                    "통과한다. 최종 방어는 unique 인덱스이므로 경쟁 조건을 반드시 검증해야 한다."
                ),
                severity="high",
                category="concurrency",
            ),
            Flaw(
                id="f3",
                text=(
                    "unique 인덱스 위반(IntegrityError)을 잡아 409로 변환하지 않으면 동시 가입 시 "
                    "사용자에게 500이 그대로 노출된다."
                ),
                severity="medium",
                category="error_handling",
            ),
            Flaw(
                id="f4",
                text=(
                    "이메일 형식 자체(@·도메인 등)에 대한 검증이 없어 "
                    "잘못된 값이 그대로 저장된다."
                ),
                severity="medium",
                category="validation",
            ),
            Flaw(
                id="f5",
                text=(
                    "'이미 존재하는 이메일'이라는 응답이 특정 이메일의 가입 여부를 노출해 계정 "
                    "열거(account enumeration)에 악용될 수 있다."
                ),
                severity="low",
                category="security",
            ),
            Flaw(
                id="f6",
                text=(
                    "비밀번호 해싱·최소 강도 정책이 명시돼 있지 않아 "
                    "평문 저장·약한 비밀번호가 통과할 수 있다."
                ),
                severity="medium",
                category="security",
            ),
        ),
    ),
    # ----- 보통 (medium) -----------------------------------------------------
    Problem(
        id="problem_003",
        title="결제 환불 처리 (Stripe webhook)",
        difficulty="medium",
        spec=(
            "결제 서비스의 환불 기능이다. 사용자가 환불을 요청하면 백엔드가 Stripe에 refund를 "
            "생성하고, 실제 환불 확정은 Stripe가 보내는 webhook('charge.refunded')으로 비동기 "
            "통보된다. webhook을 받으면 해당 주문 상태를 'refunded'로 바꾸고 사용자에게 알림을 "
            "보낸다."
        ),
        flaws=(
            Flaw(
                id="f1",
                text=(
                    "Stripe-Signature 헤더를 검증하지 않으면 위조된 webhook 요청으로 임의 주문을 "
                    "환불 처리시킬 수 있다."
                ),
                severity="high",
                category="security",
            ),
            Flaw(
                id="f2",
                text=(
                    "webhook은 재시도로 같은 이벤트가 여러 번 도착할 수 있다. event id 기반 멱등 "
                    "처리가 없으면 상태·알림이 중복 처리된다."
                ),
                severity="high",
                category="concurrency",
            ),
            Flaw(
                id="f3",
                text=(
                    "webhook이 refund 생성 응답보다 먼저 도착하는 등 순서가 역전될 수 있어, 아직 "
                    "기록되지 않은 주문에 대한 이벤트 처리를 검증해야 한다."
                ),
                severity="medium",
                category="concurrency",
            ),
            Flaw(
                id="f4",
                text=(
                    "부분 환불 금액을 무시하고 주문을 무조건 'refunded'로 바꾸면 실제 환불 금액과 "
                    "주문 상태가 어긋난다."
                ),
                severity="medium",
                category="correctness",
            ),
            Flaw(
                id="f5",
                text=(
                    "처리 도중 실패했는데 200을 너무 일찍 반환하면 Stripe가 재시도하지 않아 "
                    "이벤트가 유실된다. 실패 시 5xx로 재시도를 유도해야 한다."
                ),
                severity="medium",
                category="error_handling",
            ),
            Flaw(
                id="f6",
                text=(
                    "알림 전송 실패가 주문 상태 갱신을 롤백시키면 안 된다. 상태 변경과 알림의 "
                    "트랜잭션 경계를 검증해야 한다."
                ),
                severity="low",
                category="data_integrity",
            ),
        ),
    ),
    Problem(
        id="problem_004",
        title="검색 결과 커서 페이지네이션",
        difficulty="medium",
        spec=(
            "상품 검색 결과를 무한 스크롤로 보여준다. API는 'created_at DESC, id DESC'로 정렬하고, "
            "클라이언트가 마지막으로 받은 항목의 (created_at, id)를 커서로 보내면 그 다음 size개를 "
            "반환한다."
        ),
        flaws=(
            Flaw(
                id="f1",
                text=(
                    "created_at만으로 커서를 비교하면 동일 시각 항목들에서 누락·중복이 생긴다. "
                    "(created_at, id) 복합 커서로 동순위를 안정적으로 끊어야 한다."
                ),
                severity="high",
                category="correctness",
            ),
            Flaw(
                id="f2",
                text="클라이언트가 보낸 커서를 디코드·검증하지 않으면 조작·깨진 커서에 500이 난다.",
                severity="medium",
                category="validation",
            ),
            Flaw(
                id="f3",
                text=(
                    "size에 상한이 없으면 한 번에 거대한 페이지를 요청해 "
                    "DB·메모리를 고갈시킬 수 있다."
                ),
                severity="medium",
                category="boundary",
            ),
            Flaw(
                id="f4",
                text="커서가 없는 첫 페이지 요청의 동작(맨 앞부터 size개)을 정의·검증해야 한다.",
                severity="low",
                category="boundary",
            ),
            Flaw(
                id="f5",
                text=(
                    "페이징 도중 항목이 삽입·삭제되면 중복·누락이 생길 수 있다. 커서 방식의 일관성 "
                    "한계를 인지하고 검증해야 한다."
                ),
                severity="medium",
                category="data_integrity",
            ),
            Flaw(
                id="f6",
                text="(created_at, id) 복합 인덱스가 없으면 페이지가 깊어질수록 쿼리가 느려진다.",
                severity="low",
                category="performance",
            ),
        ),
    ),
    # ----- 어려움 (hard) -----------------------------------------------------
    Problem(
        id="problem_005",
        title="푸시 알림 팬아웃 (메시지 큐)",
        difficulty="hard",
        spec=(
            "소셜 서비스에서 사용자가 게시물을 올리면 팔로워 전원에게 푸시 알림을 보낸다. 게시 "
            "시점에 알림 작업을 메시지 큐에 넣고, 수평 확장된 워커들이 큐를 소비해 팔로워 목록을 "
            "조회한 뒤 각 디바이스 토큰으로 FCM/APNs 푸시를 발송한다."
        ),
        flaws=(
            Flaw(
                id="f1",
                text=(
                    "대부분의 큐는 at-least-once라 같은 메시지를 두 번 전달할 수 있다. "
                    "멱등 키 없이 처리하면 동일 알림이 중복 발송된다."
                ),
                severity="high",
                category="concurrency",
            ),
            Flaw(
                id="f2",
                text=(
                    "팔로워가 수백만인 셀럽 게시물을 단일 작업으로 처리하면 워커가 타임아웃·메모리 "
                    "초과로 죽는다. 팔로워를 청크로 분할해야 한다."
                ),
                severity="high",
                category="performance",
            ),
            Flaw(
                id="f3",
                text=(
                    "일부 토큰 발송이 실패했다고 작업 전체를 재시도하면 이미 성공한 대상에게 중복 "
                    "발송된다. 체크포인트·개별 재시도가 필요하다."
                ),
                severity="high",
                category="error_handling",
            ),
            Flaw(
                id="f4",
                text=(
                    "제공자가 만료/해지(404·410)로 응답한 무효 토큰을 정리하지 않으면 "
                    "실패가 계속 쌓인다."
                ),
                severity="medium",
                category="data_integrity",
            ),
            Flaw(
                id="f5",
                text=(
                    "작업 적재 시점과 실제 발송 시점 사이에 언팔로우·차단이 일어날 수 있어, 발송 "
                    "직전의 관계 상태를 반영해야 한다."
                ),
                severity="medium",
                category="correctness",
            ),
            Flaw(
                id="f6",
                text="FCM/APNs의 rate limit을 초과하면 차단되므로 throttling·backoff가 필요하다.",
                severity="medium",
                category="performance",
            ),
            Flaw(
                id="f7",
                text=(
                    "처리 불가능한 독성 메시지가 큐를 막지 않도록 "
                    "DLQ(dead-letter queue)가 필요하다."
                ),
                severity="low",
                category="error_handling",
            ),
        ),
    ),
    Problem(
        id="problem_006",
        title="주문 재고 차감 (낙관적 락)",
        difficulty="hard",
        spec=(
            "커머스 서비스의 주문 처리다. 사용자가 상품을 주문하면 products.stock에서 수량만큼 "
            "차감한다. 동시 주문 충돌을 막기 위해 낙관적 락(version 컬럼)을 쓴다: 현재 stock과 "
            "version을 읽고, version이 그대로일 때만 stock을 줄이고 version을 +1 하는 UPDATE를 "
            "실행한다."
        ),
        flaws=(
            Flaw(
                id="f1",
                text=(
                    "stock < 주문수량 검증이 없으면 재고가 음수가 되어 "
                    "초과 판매(overselling)가 발생한다."
                ),
                severity="high",
                category="correctness",
            ),
            Flaw(
                id="f2",
                text=(
                    "version 불일치로 UPDATE가 0행을 갱신했을 때(낙관적 락 충돌) "
                    "재시도·실패 처리가 없으면 주문이 조용히 누락된다."
                ),
                severity="high",
                category="concurrency",
            ),
            Flaw(
                id="f3",
                text=(
                    "결제 재시도·더블클릭으로 같은 주문이 두 번 들어오면 재고가 이중 차감된다. "
                    "주문 멱등 키가 필요하다."
                ),
                severity="high",
                category="concurrency",
            ),
            Flaw(
                id="f4",
                text=(
                    "여러 품목 주문에서 일부만 차감되고 중간에 실패하면, "
                    "트랜잭션 경계 없이는 재고가 부분 차감된 채 남는다."
                ),
                severity="medium",
                category="data_integrity",
            ),
            Flaw(
                id="f5",
                text=(
                    "주문 취소 시 재고 복원의 정확성(이중 복원·취소 후 재취소 방지)을 "
                    "검증해야 한다."
                ),
                severity="medium",
                category="correctness",
            ),
            Flaw(
                id="f6",
                text=(
                    "경합이 심하면 낙관적 락 재시도가 폭주할 수 있어 "
                    "재시도 상한·백오프가 필요하다."
                ),
                severity="medium",
                category="performance",
            ),
            Flaw(
                id="f7",
                text="주문 수량이 0 이하인 요청에 대한 검증이 없으면 비정상 주문이 통과한다.",
                severity="low",
                category="validation",
            ),
        ),
    ),
)

PROBLEM_COUNT = len(PROBLEMS)


def get_problem(index: int) -> Problem:
    """Return the problem at ``index`` (0-based). Raises IndexError if out of range."""
    return PROBLEMS[index]


def find_problem(problem_id: str) -> Problem | None:
    return next((p for p in PROBLEMS if p.id == problem_id), None)
