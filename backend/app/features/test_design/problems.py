"""Fixed, human-authored problems for the test-design evaluation.

Each problem is a short Python function whose code violates its spec in a few
specific ways. The `flaws` tuple is the **hidden ground truth**: the set of
defects a strong test designer should catch. It is never serialized to the
candidate — only `spec` and `code` are shown. The same five problems are given
to every candidate so results are comparable.

Authored as version-controlled Python constants (mirrors the rejection_eval
`topics.py` convention); curate/extend by editing this module.
"""

from dataclasses import dataclass
from typing import Literal

Severity = Literal["low", "medium", "high"]
FlawCategory = Literal["correctness", "edge_case", "validation", "security", "performance"]


@dataclass(frozen=True)
class Flaw:
    """One ground-truth defect a candidate is expected to find."""

    id: str
    text: str
    severity: Severity
    category: FlawCategory


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    spec: str
    code: str
    flaws: tuple[Flaw, ...]


PROBLEMS: tuple[Problem, ...] = (
    Problem(
        id="problem_001",
        title="average — 리스트 평균",
        spec=(
            "숫자 리스트의 산술 평균을 반환한다. 입력은 정수/실수로 이루어진 리스트이며, "
            "빈 리스트나 숫자가 아닌 원소 같은 경계 상황도 안전하게 처리해야 한다."
        ),
        code=(
            "def average(numbers):\n"
            "    total = 0\n"
            "    for n in numbers:\n"
            "        total += n\n"
            "    return total / len(numbers)\n"
        ),
        flaws=(
            Flaw(
                id="f1",
                text="빈 리스트를 넘기면 len(numbers)==0 이라 ZeroDivisionError가 발생한다.",
                severity="high",
                category="edge_case",
            ),
            Flaw(
                id="f2",
                text="원소가 숫자인지 검증하지 않아 문자열 등이 섞이면 TypeError가 난다.",
                severity="medium",
                category="validation",
            ),
            Flaw(
                id="f3",
                text="None이나 리스트가 아닌 입력에 대한 방어가 없어 예외가 그대로 전파된다.",
                severity="low",
                category="validation",
            ),
        ),
    ),
    Problem(
        id="problem_002",
        title="is_palindrome — 회문 판별",
        spec=(
            "문자열이 회문인지 판별한다. 대소문자를 구분하지 않고, 공백은 무시해야 한다. "
            "예: 'Race car' → True."
        ),
        code=(
            "def is_palindrome(s):\n"
            "    return s == s[::-1]\n"
        ),
        flaws=(
            Flaw(
                id="f1",
                text=(
                    "대소문자를 구분하지 않아야 하는데 소문자화를 하지 않아 "
                    "'Race car'가 False가 된다."
                ),
                severity="high",
                category="correctness",
            ),
            Flaw(
                id="f2",
                text="공백을 무시해야 하는데 제거하지 않아 'race car'가 False가 된다.",
                severity="high",
                category="correctness",
            ),
            Flaw(
                id="f3",
                text="None 입력 시 s[::-1]에서 TypeError가 발생한다(방어 없음).",
                severity="low",
                category="validation",
            ),
        ),
    ),
    Problem(
        id="problem_003",
        title="binary_search — 이진 탐색",
        spec=(
            "오름차순 정렬된 리스트에서 target의 인덱스를 반환하고, 없으면 -1을 반환한다."
        ),
        code=(
            "def binary_search(arr, target):\n"
            "    low, high = 0, len(arr)\n"
            "    while low < high:\n"
            "        mid = (low + high) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1\n"
        ),
        flaws=(
            Flaw(
                id="f1",
                text=(
                    "high를 len(arr)로 시작(배타적)했으면서 else에서 high=mid-1로 줄여 경계 처리가 "
                    "뒤섞인다. 마지막 원소가 target일 때 탐색 구간에서 누락돼 -1을 반환할 수 있다."
                ),
                severity="high",
                category="correctness",
            ),
            Flaw(
                id="f2",
                text="중복 원소가 있을 때 첫 번째 인덱스를 보장하지 않고 임의의 위치를 반환한다.",
                severity="medium",
                category="correctness",
            ),
            Flaw(
                id="f3",
                text="입력이 실제로 정렬돼 있는지 가정만 하고 검증하지 않는다.",
                severity="low",
                category="validation",
            ),
        ),
    ),
    Problem(
        id="problem_004",
        title="parse_int_list — 정수 파싱",
        spec=(
            "쉼표로 구분된 정수 문자열을 정수 리스트로 변환한다. 예: '1,2,3' → [1, 2, 3]. "
            "빈 문자열, 후행 쉼표, 정수가 아닌 토큰 같은 잘못된 입력도 안전하게 처리해야 한다."
        ),
        code=(
            "def parse_int_list(s):\n"
            "    return [int(x) for x in s.split(',')]\n"
        ),
        flaws=(
            Flaw(
                id="f1",
                text="빈 문자열 ''은 split이 ['']을 반환해 int('')에서 ValueError가 발생한다.",
                severity="high",
                category="edge_case",
            ),
            Flaw(
                id="f2",
                text="'1,2,' 같은 후행 쉼표는 빈 토큰을 만들어 int('')에서 ValueError가 발생한다.",
                severity="medium",
                category="edge_case",
            ),
            Flaw(
                id="f3",
                text=(
                    "'1,a' 처럼 정수가 아닌 토큰에 대한 검증/처리가 없어 "
                    "ValueError가 그대로 난다."
                ),
                severity="medium",
                category="validation",
            ),
            Flaw(
                id="f4",
                text="None 입력 시 split 호출에서 AttributeError가 발생한다(방어 없음).",
                severity="low",
                category="validation",
            ),
        ),
    ),
    Problem(
        id="problem_005",
        title="withdraw — 계좌 출금",
        spec=(
            "계좌 잔액에서 금액을 출금하고 남은 잔액을 반환한다. 잔액보다 큰 금액은 출금할 수 "
            "없고(초과 인출 금지), 출금 금액은 양수여야 한다."
        ),
        code=(
            "def withdraw(balance, amount):\n"
            "    balance = balance - amount\n"
            "    return balance\n"
        ),
        flaws=(
            Flaw(
                id="f1",
                text="amount > balance 인 초과 인출을 막지 않아 잔액이 음수가 될 수 있다.",
                severity="high",
                category="correctness",
            ),
            Flaw(
                id="f2",
                text="amount<=0 검증이 없어 음수 금액을 넣으면 오히려 잔액이 늘어난다.",
                severity="high",
                category="security",
            ),
            Flaw(
                id="f3",
                text=(
                    "실수(float) 금액의 정밀도/반올림 처리가 없어 "
                    "0.1+0.2 류의 오차가 누적될 수 있다."
                ),
                severity="medium",
                category="correctness",
            ),
            Flaw(
                id="f4",
                text="balance/amount의 타입 검증이 없어 숫자가 아닌 입력에 그대로 노출된다.",
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
