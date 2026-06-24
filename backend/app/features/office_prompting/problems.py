"""Fixed office-prompting problems + their ground-truth answer sets.

Each problem asks the candidate to write a PROMPT (not an answer). The candidate
sees `description` (human-facing); the LLM never does. The system fixes the
target entity (``target_entity``), so the candidate's prompt only needs to
express the filtering/joining criteria.

Ground truth is DERIVED, never hand-typed: each problem ships a ``criteria_fn``
(a pure-Python reference solver over ``datasets.DATASETS``) and ``ground_truth_ids``
is computed from it at import. This guarantees the stored answer always matches
the exact data the candidate and LLM see. Difficulty increases P1 -> P3.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from app.features.office_prompting import datasets


@dataclass(frozen=True)
class Problem:
    index: int
    title: str
    description: str  # human-facing; NEVER sent to the LLM
    target_entity: str  # e.g. "customer_id" — fixes the extraction target
    target_table: str  # table the ids belong to (for validation/UI)
    criteria_fn: Callable[[], set[str]] = field(compare=False)

    @property
    def ground_truth_ids(self) -> frozenset[str]:
        return frozenset(self.criteria_fn())


# --- reference solvers (pure Python over the seeded datasets) -----------------
def _price_by_product() -> dict[str, int]:
    return {p["product_id"]: p["price"] for p in datasets.PRODUCTS}


def _category_by_product() -> dict[str, str]:
    return {p["product_id"]: p["category"] for p in datasets.PRODUCTS}


def _customer_by_id() -> dict[str, dict]:
    return {c["customer_id"]: c for c in datasets.CUSTOMERS}


def _solve_p1() -> set[str]:
    """가전 카테고리를 2024년 3분기(7~9월)에 결제(paid)한 고객."""
    cat = _category_by_product()
    out: set[str] = set()
    for o in datasets.ORDERS:
        if o["status"] != "paid":
            continue
        if not o["order_date"].startswith("2024-"):
            continue
        month = int(o["order_date"][5:7])
        if not (7 <= month <= 9):
            continue
        if cat.get(o["product_id"]) == "가전":
            out.add(o["customer_id"])
    return out


def _solve_p2() -> set[str]:
    """2024년에 '가구'를 2건 이상 결제했고 region이 Seoul인 고객."""
    cat = _category_by_product()
    counts: dict[str, int] = {}
    for o in datasets.ORDERS:
        if o["status"] != "paid" or not o["order_date"].startswith("2024-"):
            continue
        if cat.get(o["product_id"]) == "가구":
            counts[o["customer_id"]] = counts.get(o["customer_id"], 0) + 1
    customers = _customer_by_id()
    return {
        cid
        for cid, n in counts.items()
        if n >= 2 and customers[cid]["region"] == "Seoul"
    }


def _solve_p3() -> set[str]:
    """2024년 결제금액(quantity*price) 합 >= 100만원, 환불 없음, segment != enterprise."""
    price = _price_by_product()
    spend: dict[str, int] = {}
    refunded: set[str] = set()
    for o in datasets.ORDERS:
        if not o["order_date"].startswith("2024-"):
            continue
        if o["status"] == "refunded":
            refunded.add(o["customer_id"])
            continue
        if o["status"] != "paid":
            continue
        amount = o["quantity"] * price[o["product_id"]]
        spend[o["customer_id"]] = spend.get(o["customer_id"], 0) + amount
    customers = _customer_by_id()
    return {
        cid
        for cid, total in spend.items()
        if total >= 1_000_000
        and cid not in refunded
        and customers[cid]["segment"] != "enterprise"
    }


PROBLEMS: tuple[Problem, ...] = (
    Problem(
        index=0,
        title="3분기 가전 구매 고객 찾기",
        description=(
            "마케팅팀이 2024년 3분기(7~9월)에 '가전' 카테고리 상품을 "
            "실제 결제(status=paid)한 고객에게 가전 사은품을 보내려 합니다. "
            "대상 고객을 모두 찾아주세요. (취소·환불 주문은 제외)"
        ),
        target_entity="customer_id",
        target_table="customers",
        criteria_fn=_solve_p1,
    ),
    Problem(
        index=1,
        title="서울 거주 가구 단골 고객",
        description=(
            "2024년 한 해 동안 '가구' 카테고리를 2건 이상 결제(paid)했고, "
            "거주 지역(region)이 'Seoul'인 단골 고객을 찾아주세요. "
            "(같은 해 서로 다른 주문 2건 이상)"
        ),
        target_entity="customer_id",
        target_table="customers",
        criteria_fn=_solve_p2,
    ),
    Problem(
        index=2,
        title="우량 고객(VIP) 선별",
        description=(
            "2024년 누적 결제금액(결제 주문의 수량×단가 합계)이 100만원 이상이면서, "
            "2024년에 환불(refunded) 주문이 한 번도 없고, 세그먼트(segment)가 "
            "'enterprise'가 아닌 우량 고객을 선별해주세요."
        ),
        target_entity="customer_id",
        target_table="customers",
        criteria_fn=_solve_p3,
    ),
)

PROBLEM_COUNT = len(PROBLEMS)
