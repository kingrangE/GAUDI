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
    # Basic tests assumed to be ALREADY implemented — shown to the candidate as a
    # starting point. Not graded; the candidate designs verification *beyond* these.
    provided_tests: tuple[str, ...]
    # The hidden answer set: the *additional* edge cases the candidate must design.
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
        provided_tests=(
            "정상 형식·적정 크기 이미지를 발급받은 URL로 업로드하면 성공한다.",
            "업로드 완료 콜백의 key로 만든 이미지 URL이 사용자 프로필에 저장된다.",
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
        provided_tests=(
            "신규 이메일로 가입하면 201로 성공하고 users에 레코드가 생긴다.",
            "이미 가입된 이메일(같은 문자열)로 다시 요청하면 중복으로 거부된다.",
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
        provided_tests=(
            "정상 환불 요청을 받으면 Stripe에 refund가 생성된다.",
            "charge.refunded webhook을 받으면 해당 주문 상태가 refunded로 바뀐다.",
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
        provided_tests=(
            "커서 없이 요청하면 최신순으로 첫 size개를 반환한다.",
            "마지막 항목의 커서를 보내면 그 다음 size개를 이어서 반환한다.",
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
        provided_tests=(
            "게시물을 작성하면 알림 작업이 메시지 큐에 적재된다.",
            "워커가 작업을 소비해 팔로워의 디바이스 토큰으로 푸시를 발송한다.",
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
        provided_tests=(
            "재고가 충분할 때 주문하면 stock이 수량만큼 줄고 version이 +1 된다.",
            "정상 주문이 성공으로 처리된다.",
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
    # ----- 어려움 (hard) — cx-churn-radar -----------------------------------
    Problem(
        id="cx-churn-radar",
        title="고객 이탈 스코어링 파이프라인 / Top-N API",
        difficulty="hard",
        spec=(
            "구독형 커머스 고객사 CX AXOps팀의 '고객 이탈 스코어링 파이프라인 / Top-N API'다. "
            "events 테이블(customer_token, event_type∈{view,cart,purchase,login,"
            "support_ticket,refund,cancel}, ts [Unix seconds, UTC], session_id, metadata)과 "
            "customers 테이블(customer_token, signup_ts, plan, region, last_active_ts)을 사용한다. "
            "PII 평문 노출은 금지 정책이다.\n\n"
            "파이프라인은 주기적으로(또는 온디맨드로) 실행된다. 각 고객에 대해 "
            "'현재 시각 기준 최근 W일(기본 30)' 윈도우 내 이벤트를 집계해 이탈 스코어를 "
            "계산한다: raw = max(0, Σweight(부정신호) − Σweight(긍정신호)), "
            "score = min(1.0, raw / NORM_FACTOR). "
            "부정 신호: support_ticket·refund·cancel(각 가중치 상이). "
            "긍정 신호: purchase·view·cart. "
            "계산된 스코어는 customers 테이블에 upsert된다.\n\n"
            "Top-N API(GET /churn/top?n=&w=)는 이탈 스코어 내림차순 상위 N명을 반환한다. "
            "프로덕션 데이터에는 결측 ts, 늦게 도착하는 이벤트(late-arriving), 중복 레코드, "
            "향후 추가될 수 있는 신규 event_type이 존재한다고 알려져 있다."
        ),
        provided_tests=(
            "최근 W일 이내 cancel·support_ticket이 다수인 고객이 이벤트가 없는 고객보다 "
            "이탈 스코어가 높다.",
            "Top-N=3 요청 시 스코어 내림차순 상위 3명만 반환된다.",
            "W 윈도우 기준 이전(ts < now − W×86400)에 발생한 이벤트는 "
            "스코어 계산에 포함되지 않는다.",
        ),
        flaws=(
            Flaw(
                id="ccr_f01",
                text=(
                    "윈도우 경계 off-by-one: ts >= now - W*86400 처리에서 정확히 W일 전에 발생한 "
                    "이벤트의 포함·제외 기준이 불명확하면 경계 이벤트가 누락되거나 이중 집계되어 "
                    "이탈 판정이 달라질 수 있다."
                ),
                severity="high",
                category="boundary",
            ),
            Flaw(
                id="ccr_f02",
                text=(
                    "결측 ts NULL 이벤트 처리 미정의: ts가 NULL인 이벤트를 그대로 비교식에 넣으면 "
                    "예외가 발생하고, epoch(0)으로 대체하면 해당 이벤트가 항상 윈도우 밖으로 "
                    "처리되어 스코어가 조용히 왜곡된다."
                ),
                severity="high",
                category="error_handling",
            ),
            Flaw(
                id="ccr_f03",
                text=(
                    "파이프라인 부분 실패 처리 미정의: 일부 고객 스코어 갱신 중 DB 오류 등으로 "
                    "실패할 때, 성공한 고객은 최신 스코어·실패한 고객은 구 스코어가 남아 "
                    "전체 Top-N 결과의 일관성이 깨진다."
                ),
                severity="medium",
                category="error_handling",
            ),
            Flaw(
                id="ccr_f04",
                text=(
                    "동시 스코어 갱신 경쟁 조건(lost update): 두 워커가 같은 customer_token의 "
                    "score를 동시에 READ-MODIFY-WRITE할 때 낙관적 락·원자적 upsert 없이 구현하면 "
                    "마지막 쓰기만 반영되어 한 워커의 계산 결과가 유실된다."
                ),
                severity="high",
                category="concurrency",
            ),
            Flaw(
                id="ccr_f05",
                text=(
                    "멱등성 부재 — 파이프라인 재실행 시 중복 집계: 처리 완료된 이벤트 범위를 "
                    "기록하는 체크포인트가 없으면, 파이프라인을 재실행할 때 동일 윈도우의 이벤트를 "
                    "다시 누적해 스코어가 부풀어 오른다."
                ),
                severity="medium",
                category="concurrency",
            ),
            Flaw(
                id="ccr_f06",
                text=(
                    "customer_token PII 평문 노출: Top-N API 응답에 customer_token을 직접 반환하면 "
                    "PII 금지 정책을 위반하고, 응답 로그·캐시에 고객 식별자가 평문으로 남아 "
                    "고객 추적이 가능해진다."
                ),
                severity="high",
                category="security",
            ),
            Flaw(
                id="ccr_f07",
                text=(
                    "접근 권한 제어(RBAC) 미비: /churn/top API에 역할 기반 권한 검증이 없으면 "
                    "관리자 외 사용자나 다른 팀도 전체 고객의 이탈 스코어 상위 목록을 "
                    "조회할 수 있어 고객 데이터가 의도치 않게 유출된다."
                ),
                severity="medium",
                category="security",
            ),
            Flaw(
                id="ccr_f08",
                text=(
                    "중복 이벤트 dedup 미적용: (customer_token, event_type, session_id, ts)가 "
                    "동일한 중복 레코드를 dedup 없이 집계하면 "
                    "부정 신호(refund·cancel·support_ticket)가 "
                    "과산정되어 이탈 스코어가 실제보다 높게 왜곡된다."
                ),
                severity="high",
                category="data_integrity",
            ),
            Flaw(
                id="ccr_f09",
                text=(
                    "늦은 도착 이벤트(late-arriving) 재계산 미트리거: 스코어 산출 이후 "
                    "late-arriving 이벤트가 삽입될 때 재계산을 트리거하지 않으면 해당 고객의 "
                    "스코어가 오래된 값으로 유지되어 Top-N 순위가 부정확해진다."
                ),
                severity="medium",
                category="data_integrity",
            ),
            Flaw(
                id="ccr_f10",
                text=(
                    "스키마 드리프트 — 신규 event_type 처리 미정의: 새 event_type이 가중치 맵에 "
                    "없을 때 KeyError가 발생하거나 묵시적으로 0으로 처리되어 "
                    "스코어가 조용히 왜곡된다. 알 수 없는 타입에 대한 명시적 거부 또는 "
                    "기본 가중치 정책을 정의해야 한다."
                ),
                severity="high",
                category="validation",
            ),
            Flaw(
                id="ccr_f11",
                text=(
                    "ts 단위·타임존 불일치: ts가 Unix milliseconds(ms)로 저장된 레코드와 "
                    "seconds(s)로 저장된 레코드가 혼재하거나 UTC 보장이 없으면 "
                    "윈도우 경계 계산이 틀려 W일 기준이 수십 년 차이로 벗어날 수 있다."
                ),
                severity="medium",
                category="validation",
            ),
            Flaw(
                id="ccr_f12",
                text=(
                    "인덱스 미비로 인한 풀스캔: events 테이블에 (customer_token, ts) 복합 인덱스가 "
                    "없으면 W-일 윈도우 필터가 전체 이벤트 로그를 스캔해, 고객 수 × 이벤트 수에 "
                    "비례한 O(N) 풀스캔이 발생해 파이프라인 실행 시간이 폭발적으로 증가한다."
                ),
                severity="high",
                category="performance",
            ),
            Flaw(
                id="ccr_f13",
                text=(
                    "비효율 Top-N 구현: 전체 고객 스코어를 ORDER BY score DESC 후 LIMIT N으로 "
                    "구현하면 수백만 고객 환경에서 O(N log N) 정렬이 매 요청마다 발생한다. "
                    "힙(heap) 또는 부분 정렬로 O(N log k)로 개선할 수 있다."
                ),
                severity="low",
                category="performance",
            ),
            Flaw(
                id="ccr_f14",
                text=(
                    "refund·cancel 오분류 — 동일 가중치 부여: refund(반품)은 부분적 불만 신호이고 "
                    "cancel(구독 해지)은 강한 이탈 확정 신호인데 동일 가중치를 부여하면 "
                    "이탈 스코어가 실제 이탈 의도를 반영하지 못해 탐지 정확도가 저하된다."
                ),
                severity="high",
                category="correctness",
            ),
            Flaw(
                id="ccr_f15",
                text=(
                    "이탈 정의의 긍정 신호 부재 조건 누락: 이탈 정의는 '부정 신호 누적 + 긍정 신호 "
                    "부재'의 복합 조건인데, 스코어 공식이 차이값만 계산하면 최근 구매(긍정 신호)가 "
                    "있어도 다수의 support_ticket으로 인해 이탈 High-risk로 오판된다."
                ),
                severity="medium",
                category="correctness",
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
