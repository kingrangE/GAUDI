"""Built-in problem registry. Real problem sourcing/licensing is an open question (SPEC).

Programmers-style: each problem ships a function stub (`starter_code`) the candidate must
complete; cases are (args -> expected return value). The non-hidden cases double as the
visible "입출력 예" shown in the UI.

All problems are hard (카카오 코딩테스트 2차 / Platinum) and span different types. Public
example answers match the official problem samples; every test (10+ per problem, with many
adversarial hidden edge cases) is re-verified by running the reference solution in
tests/test_problems_consistency.py.
"""

from __future__ import annotations

from feature_dev_prompting.models import GradingCase, Problem


# ── churn-risk-stream: deterministic builders for the large stress cases ──────
# Kept tiny and explicit so the expected values are provable by construction and
# re-verified by the reference solution in tests.
def _build_all_atrisk(customers: int, k: int) -> list[list[int]]:
    """`customers` customers, each with k negatives at ts 0..k-1 (no positives).

    Every customer enters at-risk at ts=k-1 and is never reset, so all of them are
    simultaneously at-risk at instant k-1 -> answer == customers (window >= k-1)."""
    return [[c, t, 0] for c in range(1, customers + 1) for t in range(k)]


def _build_single_allneg(count: int) -> list[list[int]]:
    """One customer with `count` negatives at ts 0..count-1 (no positives)."""
    return [[1, t, 0] for t in range(count)]


def _build_chain_with_resets(customers: int, bursts: int, k: int) -> list[list[int]]:
    """Each customer repeats `bursts` identical (k negatives then 1 positive) bursts
    on the same ts grid, so every customer shares the same at-risk episodes."""
    ev: list[list[int]] = []
    for c in range(1, customers + 1):
        ts = 0
        for _ in range(bursts):
            for _ in range(k):
                ev.append([c, ts, 0])
                ts += 1
            ev.append([c, ts, 1])
            ts += 1
    return ev


_CR_FIVE = _build_all_atrisk(5, 3)            # answer 5
_CR_DENSE300 = _build_all_atrisk(300, 3)      # answer 300
_CR_DENSE1500 = _build_all_atrisk(1500, 3)    # answer 1500
_CR_ALLNEG200K = _build_single_allneg(200000)  # answer 1
_CR_MANY200K = _build_all_atrisk(66666, 3)    # answer 66666 (n=199998)
_CR_CHAIN2000 = _build_chain_with_resets(2000, 2, 3)  # answer 2000 (n=16000)
_CR_WORKED = [
    [1, 0, 0], [1, 2, 0], [1, 3, 0],
    [2, 4, 0], [2, 5, 0], [2, 6, 0], [2, 12, 1],
    [3, 0, 0], [3, 1, 0], [3, 5, 1], [3, 6, 0], [3, 7, 0], [3, 8, 0],
]  # answer 3

_F1 = [[4, 1, 10], [3, 5, 24], [5, 6, 2], [3, 1, 41], [5, 1, 24], [4, 6, 50],
       [2, 4, 66], [2, 3, 22], [1, 6, 25]]
_F2 = [[5, 7, 9], [4, 6, 4], [3, 6, 1], [3, 2, 3], [2, 1, 6]]
_F3 = [[2, 6, 6], [6, 3, 7], [4, 6, 7], [6, 5, 11], [2, 5, 12], [5, 3, 20], [2, 4, 8], [4, 3, 9]]
_T1 = [[1, 2, 5], [2, 3, 5]]
_T2 = [[1, 2, 1], [2, 3, 1]]
_T3 = [[1, 2, 3], [2, 3, 4], [3, 4, 5], [1, 4, 10]]
_T4 = [[1, 2, 10], [1, 2, 3], [2, 3, 4]]
_T5 = [[1, 2, 1], [1, 3, 1], [1, 4, 1]]
_T6 = [[1, 2, 2], [2, 3, 2], [3, 4, 2], [4, 5, 2], [1, 5, 100]]
_INFO = ["java backend junior pizza 150", "python frontend senior chicken 210",
         "python frontend senior chicken 150", "cpp backend senior pizza 260",
         "java backend junior chicken 80", "python backend senior chicken 50"]
_QUERY = ["java and backend and junior and pizza 100",
          "python and frontend and senior and chicken 200",
          "cpp and - and senior and pizza 250", "- and backend and senior and - 150",
          "- and - and - and chicken 100", "- and - and - and - 150"]

_PROBLEMS: dict[str, Problem] = {
    # ── 그래프 (플로이드-워셜) ───────────────────────────────────────────────
    "taxi-fare": Problem(
        id="taxi-fare",
        title="합승 택시 요금",
        statement=(
            "밤늦게 당신과 친구는 같은 방향으로 가다가 갈라져 각자 집으로 갑니다. 처음에는 "
            "합승해서 함께 이동하다가 어느 지점에서 내려, 거기서부터는 각자 따로 택시를 "
            "탑니다.\n\n"
            "지점은 1번부터 n번까지 있고, fares의 각 원소 [u, v, w]는 지점 u와 v 사이를 요금 "
            "w로 오갈 수 있는 길을 뜻합니다(양방향). 출발 지점 s에서 합승해 어떤 지점 k까지 "
            "함께 간 뒤, k에서 갈라져 한 명은 a번, 다른 한 명은 b번 지점으로 갑니다.\n\n"
            "합승 구간과 각자 이동 구간을 합한 총요금이 최소가 되도록 할 때, 그 최소 요금을 "
            "return 하도록 solution 함수를 완성하세요. (s에서 곧바로 갈라져도 됩니다.)"
        ),
        constraints="3 <= n <= 200, 1 <= s, a, b <= n, 1 <= len(fares) <= 10000, 1 <= w <= 100000",
        entry_point="solution",
        starter_code=(
            "def solution(n, s, a, b, fares):\n    answer = 0\n    return answer\n"
        ),
        tests=[
            GradingCase(args=[6, 4, 6, 2, _F1], expected=82, hidden=False),
            GradingCase(args=[7, 3, 4, 1, _F2], expected=14, hidden=True),
            GradingCase(args=[6, 4, 5, 6, _F3], expected=18, hidden=True),
            GradingCase(args=[3, 1, 3, 3, _T1], expected=10, hidden=True),
            GradingCase(args=[3, 2, 2, 2, _T2], expected=0, hidden=True),     # s=a=b
            GradingCase(args=[4, 1, 4, 4, _T3], expected=10, hidden=True),    # a=b
            GradingCase(args=[3, 1, 2, 3, _T4], expected=7, hidden=True),     # 중복 간선
            GradingCase(args=[4, 2, 3, 4, _T5], expected=3, hidden=True),     # 스타 그래프
            GradingCase(args=[5, 1, 5, 3, _T6], expected=8, hidden=True),
            GradingCase(args=[5, 3, 1, 5, _T6], expected=8, hidden=True),
            GradingCase(args=[5, 5, 5, 1, _T6], expected=8, hidden=True),
        ],
    ),
    # ── 파싱 + 완전탐색(순열) ────────────────────────────────────────────────
    "max-expression": Problem(
        id="max-expression",
        title="수식 최대화",
        statement=(
            "expression은 +, -, * 세 종류의 연산자와 숫자로만 이루어진 수식 문자열입니다. "
            "원래 이 연산자들에는 정해진 우선순위가 있지만, 당신은 세 연산자의 우선순위를 "
            "원하는 순서로 새로 정할 수 있습니다.\n\n"
            "예컨대 우선순위를 (- > * > +)로 정하면 모든 -를 먼저, 그다음 *, 마지막으로 +를 "
            "계산합니다. 같은 우선순위의 연산자는 왼쪽부터 차례로 계산합니다.\n\n"
            "수식에 실제로 등장하는 연산자들의 우선순위를 어떻게 정하느냐에 따라 결과가 "
            "달라집니다. 가능한 모든 우선순위 조합으로 계산한 결과들 중 절댓값이 가장 큰 값을 "
            "return 하도록 solution 함수를 완성하세요."
        ),
        constraints="len(expression) <= 100, 숫자는 0 이상, 중간 결과의 절댓값은 매우 커질 수 있음",
        entry_point="solution",
        starter_code="def solution(expression):\n    answer = 0\n    return answer\n",
        tests=[
            GradingCase(args=["100-200*300-500+20"], expected=60420, hidden=False),
            GradingCase(args=["50*6-3*2"], expected=300, hidden=True),
            GradingCase(args=["1*2*3"], expected=6, hidden=True),
            GradingCase(args=["3-2-1"], expected=0, hidden=True),         # 같은 연산자뿐
            GradingCase(args=["123"], expected=123, hidden=True),         # 연산자 없음
            GradingCase(args=["5-3*2"], expected=4, hidden=True),         # 우선순위로 부호
            GradingCase(args=["1-2-3-4"], expected=8, hidden=True),
            GradingCase(args=["2*3*4"], expected=24, hidden=True),
            GradingCase(args=["1-1-1-1-1"], expected=3, hidden=True),
            GradingCase(args=["0-0-0"], expected=0, hidden=True),
            GradingCase(args=["2*3-4*5"], expected=14, hidden=True),
            GradingCase(args=["99*99-99"], expected=9702, hidden=True),
        ],
    ),
    # ── 원형 + 완전탐색(순열) + 그리디 ───────────────────────────────────────
    "wall-check": Problem(
        id="wall-check",
        title="외벽 점검",
        statement=(
            "둘레가 n인 원형 외벽이 있고, 취약 지점들의 위치가 weak에 시계방향 좌표로 "
            "주어집니다. 친구들을 보내 모든 취약 지점을 점검하려고 합니다. 각 친구가 한 번에 "
            "점검할 수 있는 거리는 dist에 주어집니다.\n\n"
            "한 친구는 임의의 취약 지점에서 시작해 시계방향으로 자신의 거리만큼 이동하며 그 "
            "사이의 취약 지점을 모두 점검합니다. 한 명이 점검을 마치면 다음 친구가 이어서 "
            "점검합니다.\n\n"
            "외벽은 원형이라 끝과 시작이 이어져 있습니다. 모든 취약 지점을 점검하는 데 필요한 "
            "친구 수의 최솟값을 return 하도록 solution 함수를 완성하세요. 친구를 모두 동원해도 "
            "다 점검할 수 없으면 -1을 return 합니다."
        ),
        constraints="1 <= n <= 200, 1 <= len(weak) <= 15, 1 <= len(dist) <= 8",
        entry_point="solution",
        starter_code="def solution(n, weak, dist):\n    answer = 0\n    return answer\n",
        tests=[
            GradingCase(args=[12, [1, 5, 6, 10], [1, 2, 3, 4]], expected=2, hidden=False),
            GradingCase(args=[12, [1, 3, 4, 9, 10], [3, 5, 7]], expected=1, hidden=True),
            GradingCase(args=[10, [0, 2, 4, 6, 8], [1]], expected=-1, hidden=True),    # 불가능
            GradingCase(args=[8, [0, 4], [3, 3]], expected=2, hidden=True),
            GradingCase(args=[10, [5], [1]], expected=1, hidden=True),
            GradingCase(args=[10, [1, 2, 3], [5]], expected=1, hidden=True),
            GradingCase(args=[20, [0, 5, 10, 15], [2, 2]], expected=-1, hidden=True),
            GradingCase(args=[10, [1, 9], [2]], expected=1, hidden=True),   # 시작-끝 연결
            GradingCase(args=[12, [0, 3, 6, 9], [3, 3, 3, 3]], expected=2, hidden=True),
            GradingCase(args=[100, [1, 50, 99], [50]], expected=-1, hidden=True),
            GradingCase(args=[6, [0, 1, 2, 3, 4, 5], [6]], expected=1, hidden=True),
            GradingCase(args=[6, [0, 1, 2, 3, 4, 5], [1, 1]], expected=-1, hidden=True),
        ],
    ),
    # ── 이분 탐색 / 슬라이딩 윈도우 ──────────────────────────────────────────
    "stepping-stones": Problem(
        id="stepping-stones",
        title="징검다리 건너기",
        statement=(
            "개울에 징검다리가 한 줄로 놓여 있고, 각 디딤돌에 적힌 숫자가 리스트 stones에 "
            "순서대로 주어집니다. 친구들이 한 명씩 디딤돌을 밟고 개울을 건너는데, 누군가 "
            "디딤돌을 밟을 때마다 그 디딤돌의 숫자가 1씩 줄어듭니다. 숫자가 0인 디딤돌은 밟을 "
            "수 없습니다.\n\n"
            "각 친구는 밟을 수 있는 디딤돌이 나올 때까지 앞으로 건너뛸 수 있지만, 밟을 수 "
            "없는(0인) 디딤돌이 연속으로 k개 나오면 그 친구는 더 건너지 못하고 멈춥니다.\n\n"
            "친구들이 차례로 건널 때, 무사히 건널 수 있는 친구의 최대 수를 return 하도록 "
            "solution 함수를 완성하세요."
        ),
        constraints="1 <= len(stones) <= 200000, 1 <= 각 숫자 <= 200000000, 1 <= k <= len(stones)",
        entry_point="solution",
        starter_code="def solution(stones, k):\n    answer = 0\n    return answer\n",
        tests=[
            GradingCase(args=[[2, 4, 5, 3, 2, 1, 4, 2, 5, 1], 3], expected=3, hidden=False),
            GradingCase(args=[[1], 1], expected=1, hidden=True),
            GradingCase(args=[[3, 3, 3], 1], expected=3, hidden=True),
            GradingCase(args=[[5, 1, 1, 1, 5], 2], expected=1, hidden=True),
            GradingCase(args=[[7, 7, 7, 7], 2], expected=7, hidden=True),
            GradingCase(args=[[2, 5, 3], 3], expected=5, hidden=True),       # k=len → 최댓값
            GradingCase(args=[[1, 2, 3, 4, 5], 2], expected=2, hidden=True),
            GradingCase(args=[[5, 4, 3, 2, 1], 2], expected=2, hidden=True),
            GradingCase(args=[[10, 10, 1, 10, 10], 3], expected=10, hidden=True),  # 1은 안 걸림
            GradingCase(args=[[1, 10, 10, 10, 1], 1], expected=1, hidden=True),
            GradingCase(args=[[100], 1], expected=100, hidden=True),
            GradingCase(args=[[2, 1, 2, 1, 2], 2], expected=2, hidden=True),
        ],
    ),
    # ── 조합 전개 + 정렬 + 이분 탐색 ─────────────────────────────────────────
    "ranking-search": Problem(
        id="ranking-search",
        title="순위 검색",
        statement=(
            "개발자 지원자들의 정보가 info에 주어집니다. 각 지원자 정보는 \"언어 직군 경력 "
            "소울푸드 점수\" 다섯 항목이 공백으로 구분된 문자열입니다(앞 네 항목은 조건, 마지막은 "
            "점수).\n\n"
            "질의 목록 query가 주어지며, 각 질의는 \"언어 and 직군 and 경력 and 소울푸드 X\" "
            "형태로, 네 조건을 모두 만족하면서 점수가 X 이상인 지원자가 몇 명인지 묻습니다. "
            "조건 항목이 \"-\"이면 그 항목은 아무 값이나 상관없음을 뜻합니다.\n\n"
            "각 질의에 대해 조건을 만족하는 지원자 수를 질의 순서대로 리스트에 담아 return 하도록 "
            "solution 함수를 완성하세요. 질의가 매우 많으므로 효율적으로 처리해야 합니다."
        ),
        constraints="1 <= len(info) <= 50000, 1 <= len(query) <= 100000, 점수 <= 100000",
        entry_point="solution",
        starter_code="def solution(info, query):\n    answer = []\n    return answer\n",
        tests=[
            GradingCase(args=[_INFO, _QUERY], expected=[1, 1, 1, 1, 2, 4], hidden=False),
            GradingCase(
                args=[["a b c d 100"], ["a and b and c and d 100", "a and b and c and d 101"]],
                expected=[1, 0],
                hidden=True,
            ),
            GradingCase(args=[_INFO, ["- and - and - and - 0"]], expected=[6], hidden=True),
            GradingCase(
                args=[["x y z w 50"], ["x and y and z and w 50", "x and y and z and w 51"]],
                expected=[1, 0],
                hidden=True,
            ),
            GradingCase(
                args=[["a b c d 100"], ["e and - and - and - 0"]], expected=[0], hidden=True
            ),
            GradingCase(
                args=[["a b c d 100", "a b c d 200"], ["a and - and - and - 150"]],
                expected=[1],
                hidden=True,
            ),
            GradingCase(args=[_INFO, ["- and backend and - and - 0"]], expected=[4], hidden=True),
            GradingCase(
                args=[_INFO, ["python and - and senior and - 100"]], expected=[2], hidden=True
            ),
            GradingCase(args=[_INFO, ["- and - and - and pizza 300"]], expected=[0], hidden=True),
            GradingCase(
                args=[_INFO, ["java and backend and junior and - 80"]], expected=[2], hidden=True
            ),
        ],
    ),
    # ── 이진 탐색 + 2D 누적합 (2025 카카오 2차) ──────────────────────────────
    "cactus-hide": Problem(
        id="cactus-hide",
        title="선인장 숨기기",
        statement=(
            "m개의 행과 n개의 열로 된 격자가 사막 지도로 주어집니다. 왼쪽 위 칸이 (0,0), "
            "오른쪽 아래 칸이 (m-1, n-1)입니다. 이 사막에 세로 h, 가로 w 크기의 선인장 구역을 "
            "두려고 합니다. 선인장 구역은 축에 맞춘 연속된 h×w 부분 격자이며 회전할 수 "
            "없습니다.\n\n"
            "비구름이 정해진 순서대로 여러 칸에 비를 뿌립니다(drops, 모두 서로 다른 칸). "
            "빗방울이 처음으로 선인장 구역 안의 칸에 떨어진 순간을 선인장이 처음 비를 맞는 "
            "시점으로 봅니다. 선인장이 가능한 한 늦게 비를 맞도록 구역의 위치를 정하세요.\n\n"
            "아예 비를 맞지 않게 둘 수 있다면 그 위치를 가장 우선합니다. 가장 늦게 비를 맞는 "
            "후보가 여럿이면 가장 위쪽 행, 그래도 여럿이면 가장 왼쪽 열을 고릅니다.\n\n"
            "정수 m, n, h, w와 빗방울 좌표가 떨어진 순서대로 담긴 2차원 정수 배열 drops"
            "(각 원소 [r, c])가 주어집니다. 조건을 만족하는 선인장 구역의 가장 왼쪽 위 칸 "
            "좌표 [r, c]를 return 하도록 solution 함수를 완성하세요."
        ),
        constraints=(
            "1 <= m, n; 1 <= m*n <= 500000; 1 <= h <= m; 1 <= w <= n; "
            "1 <= len(drops) <= m*n; 0 <= r < m, 0 <= c < n; drops의 칸은 모두 서로 다름"
        ),
        entry_point="solution",
        starter_code="def solution(m, n, h, w, drops):\n    answer = [0, 0]\n    return answer\n",
        time_limit_sec=5.0,
        tests=[
            GradingCase(
                args=[4, 5, 2, 2,
                      [[0, 0], [3, 1], [1, 3], [2, 4], [1, 1], [2, 2], [2, 3], [0, 4]]],
                expected=[2, 2],
                hidden=False,
            ),
            GradingCase(
                args=[3, 3, 1, 1, [[0, 0], [0, 1], [0, 2], [1, 0]]], expected=[1, 1], hidden=False
            ),
            GradingCase(args=[4, 6, 3, 4, [[1, 2]]], expected=[0, 0], hidden=False),
            GradingCase(
                args=[4, 6, 1, 2,
                      [[0, 1], [0, 3], [0, 5], [1, 1], [1, 3], [1, 5],
                       [2, 1], [2, 3], [2, 5], [3, 1], [3, 3], [3, 5]]],
                expected=[3, 4],
                hidden=True,
            ),
            GradingCase(
                args=[2, 2, 2, 2, [[0, 0], [0, 1], [1, 1], [1, 0]]], expected=[0, 0], hidden=True
            ),
            GradingCase(
                args=[4, 4, 3, 1, [[2, 0], [1, 3], [3, 2], [0, 1]]], expected=[0, 2], hidden=True
            ),
            GradingCase(args=[3, 3, 1, 1, [[0, 0]]], expected=[0, 1], hidden=True),  # 안 젖음 우선
            GradingCase(args=[4, 4, 2, 2, [[0, 0]]], expected=[0, 1], hidden=True),
            GradingCase(args=[1, 5, 1, 1, [[0, 2], [0, 0]]], expected=[0, 1], hidden=True),
            GradingCase(
                args=[3, 3, 2, 2, [[0, 0], [2, 2], [0, 2], [2, 0]]], expected=[1, 0], hidden=True
            ),
            GradingCase(
                args=[2, 2, 1, 1, [[0, 0], [1, 1], [0, 1], [1, 0]]], expected=[1, 0], hidden=True
            ),
        ],
    ),
    # ── 이벤트 스트림 + 슬라이딩 윈도우(고객별) + 스위프라인 (플래티넘 상위급) ──────
    "churn-risk-stream": Problem(
        id="churn-risk-stream",
        title="이탈 위험 고객 최대 동시 인원",
        statement=(
            "구독형 커머스 고객사의 CX 로그를 분석해 '이탈 위험' 고객을 추적하는 Customer "
            "AXOps팀의 대시보드를 만듭니다. 로그는 n개의 이벤트로 이루어지며, 각 이벤트는 "
            "[customer_id, ts, type] 형식입니다. ts는 발생 시각(정수), type은 0이면 부정 "
            "이벤트(환불·문의 등 이탈 신호), 1이면 긍정 이벤트(구매·로그인 등 재참여 신호)입니다. "
            "이벤트는 시간 순서대로 주어지지 않을 수 있습니다.\n\n"
            "한 고객의 이벤트는 ts 오름차순으로 처리하며, ts가 같으면 부정(0)을 긍정(1)보다 먼저 "
            "처리합니다.\n\n"
            "[위험 진입] 한 고객이 길이 window 이하의 구간 안에 부정 이벤트를 k개 이상 쌓는 순간, "
            "즉 부정 이벤트 k개의 ts 최댓값과 최솟값의 차이가 window 이하가 되는 순간 그 고객은 "
            "'이탈 위험' 상태가 됩니다(구간 양 끝 포함). 위험에 진입하는 시각은 그 조건을 처음 "
            "만족시킨 k번째 부정 이벤트의 ts입니다.\n\n"
            "[위험 해제·초기화] 긍정 이벤트는 그 고객의 위험 상태를 해제하고, 그때까지 "
            "누적된 부정 이벤트 기록을 모두 초기화합니다(위험 상태가 아니었더라도 기록은 "
            "초기화됩니다). 즉 긍정 이벤트 이후에는 다시 새로 k개의 부정 이벤트가 window "
            "안에 쌓여야 위험 상태가 됩니다. 해제되는 시각은 그 긍정 이벤트의 ts입니다.\n\n"
            "따라서 한 번의 위험 구간은 반열린 구간 [진입 ts, 해제 ts)로 봅니다. 해제되는 "
            "ts 시점에는 이미 위험 상태가 아닙니다. 진입 후 긍정 이벤트가 더 없으면 그 고객은 "
            "그 시각 이후로 계속 위험 상태입니다. (한 고객의 k번째 부정 이벤트와 긍정 "
            "이벤트의 ts가 같으면 진입과 해제가 같은 시각이 되어 그 순간에는 위험으로 세지 "
            "않습니다.)\n\n"
            "어느 한 시점에 동시에 '이탈 위험' 상태인 고객 수의 최댓값을 return 하도록 "
            "solution 함수를 완성하세요.\n\n"
            "[예시] window=5, k=3 이고 events가 아래와 같을 때:\n"
            "  customer 1: 부정 ts=0,2,3 → 세 부정(0,2,3)의 ts 폭이 3(≤5)이라 ts=3에 위험 진입, "
            "이후 긍정 없음 → [3, ∞)\n"
            "  customer 2: 부정 ts=4,5,6 → ts=6에 위험 진입, 긍정 ts=12에 해제 → [6, 12)\n"
            "  customer 3: 부정 ts=0,1 → 긍정 ts=5로 초기화 → 부정 ts=6,7,8 → ts=8에 위험 진입 → "
            "[8, ∞)\n"
            "ts=8 시점에 customer 1·2·3이 모두 위험 상태이므로 동시 위험 인원의 최댓값은 3입니다."
        ),
        constraints=(
            "0 <= n <= 200000, n == len(events); 1 <= customer_id <= 10^9; 0 <= ts <= 10^9; "
            "type ∈ {0, 1}; 0 <= window <= 10^9; 1 <= k <= 200000. 이벤트 순서는 보장되지 않음."
        ),
        entry_point="solution",
        starter_code="def solution(n, events, window, k):\n    answer = 0\n    return answer\n",
        time_limit_sec=6.0,
        tests=[
            # ── 공개 예제 (hidden=False) ──────────────────────────────────────
            # 본문 예시: 세 고객, ts=8에 동시 3명
            GradingCase(args=[13, _CR_WORKED, 5, 3], expected=3, hidden=False),
            # 정확히 k개 → 1명
            GradingCase(args=[3, [[7, 1, 0], [7, 2, 0], [7, 3, 0]], 10, 3],
                        expected=1, hidden=False),
            # 한 명만 위험, 다른 한 명은 window 초과
            GradingCase(args=[4, [[1, 0, 0], [1, 3, 0], [2, 0, 0], [2, 5, 0]], 4, 2],
                        expected=1, hidden=False),
            # 동일 ts 3개 + window=0
            GradingCase(args=[3, [[1, 5, 0], [1, 5, 0], [1, 5, 0]], 0, 3],
                        expected=1, hidden=False),
            # ── 숨김 케이스 (hidden=True) ─────────────────────────────────────
            # 빈 입력
            GradingCase(args=[0, [], 5, 3], expected=0, hidden=True),
            # k=1 단일 부정
            GradingCase(args=[1, [[1, 4, 0]], 5, 1], expected=1, hidden=True),
            # 부정 1개 < k
            GradingCase(args=[1, [[1, 4, 0]], 5, 2], expected=0, hidden=True),
            # 긍정뿐
            GradingCase(args=[1, [[1, 4, 1]], 5, 1], expected=0, hidden=True),
            # 전부 긍정
            GradingCase(args=[4, [[1, 0, 1], [1, 1, 1], [2, 2, 1], [3, 3, 1]], 100, 1],
                        expected=0, hidden=True),
            # 전부 부정, 정확히 k
            GradingCase(args=[3, [[1, 0, 0], [1, 1, 0], [1, 2, 0]], 100, 3],
                        expected=1, hidden=True),
            # k-1개
            GradingCase(args=[2, [[1, 0, 0], [1, 1, 0]], 100, 3], expected=0, hidden=True),
            # 폭 == window (경계 포함 → 진입)
            GradingCase(args=[3, [[1, 0, 0], [1, 4, 0], [1, 8, 0]], 8, 3],
                        expected=1, hidden=True),
            # 폭 == window+1 (미달)
            GradingCase(args=[3, [[1, 0, 0], [1, 4, 0], [1, 9, 0]], 8, 3],
                        expected=0, hidden=True),
            # 같은 ts 긍정이 진입을 즉시 해제 ([2,2) 공집합)
            GradingCase(args=[4, [[1, 0, 0], [1, 1, 0], [1, 2, 0], [1, 2, 1]], 5, 3],
                        expected=0, hidden=True),
            # 진입 직후(+1) 긍정 → [2,3)
            GradingCase(args=[4, [[1, 0, 0], [1, 1, 0], [1, 2, 0], [1, 3, 1]], 5, 3],
                        expected=1, hidden=True),
            # 긍정 초기화 후 재진입
            GradingCase(args=[6, [[1, 0, 0], [1, 1, 0], [1, 5, 1], [1, 6, 0], [1, 7, 0],
                                  [1, 8, 0]], 5, 3], expected=1, hidden=True),
            # 긍정 초기화로 진입 못 함
            GradingCase(args=[4, [[1, 0, 0], [1, 1, 0], [1, 2, 1], [1, 3, 0]], 5, 3],
                        expected=0, hidden=True),
            # 5명 동시
            GradingCase(args=[15, _CR_FIVE, 5, 3], expected=5, hidden=True),
            # 시차 → 비중첩
            GradingCase(args=[6, [[1, 0, 0], [1, 1, 0], [1, 2, 1], [2, 10, 0], [2, 11, 0],
                                  [2, 12, 0]], 5, 3], expected=1, hidden=True),
            # window=0, ts 모두 다름
            GradingCase(args=[3, [[1, 0, 0], [1, 1, 0], [1, 2, 0]], 0, 3],
                        expected=0, hidden=True),
            # k == 세그먼트 길이
            GradingCase(args=[4, [[1, 0, 0], [1, 1, 0], [1, 2, 0], [1, 3, 0]], 100, 4],
                        expected=1, hidden=True),
            # k=1, 긍정 사이의 단일 부정
            GradingCase(args=[4, [[1, 0, 1], [1, 1, 1], [1, 2, 0], [1, 3, 1]], 5, 1],
                        expected=1, hidden=True),
            # 한 고객 여러 에피소드 → 한 고객은 동시 최대 1
            GradingCase(args=[8, [[1, 0, 0], [1, 1, 0], [1, 2, 1], [1, 3, 0], [1, 4, 0],
                                  [1, 5, 1], [1, 6, 0], [1, 7, 0]], 10, 2],
                        expected=1, hidden=True),
            # 열린 구간 + 닫힌 구간 중첩
            GradingCase(args=[5, [[1, 0, 0], [1, 1, 0], [2, 1, 0], [2, 2, 0], [2, 9, 1]], 10, 2],
                        expected=2, hidden=True),
            # 입력 순서가 뒤섞임 → 고객별 정렬 필요
            GradingCase(args=[6, [[2, 6, 0], [1, 3, 0], [2, 4, 0], [1, 1, 0], [2, 5, 0],
                                  [1, 2, 0]], 5, 3], expected=2, hidden=True),
            # 고객 간 동일 ts
            GradingCase(args=[6, [[1, 5, 0], [2, 5, 0], [1, 5, 0], [2, 5, 0], [1, 5, 0],
                                  [2, 5, 0]], 0, 3], expected=2, hidden=True),
            # 해제 ts == 다른 고객 진입 ts 경계 (반열린 → 동시 아님)
            GradingCase(args=[7, [[1, 0, 0], [1, 1, 0], [1, 2, 0], [1, 5, 1], [2, 3, 0],
                                  [2, 4, 0], [2, 5, 0]], 5, 3], expected=1, hidden=True),
            # 중간 피크
            GradingCase(args=[10, [[1, 0, 0], [1, 1, 0], [1, 2, 0], [1, 4, 1], [2, 1, 0],
                                   [2, 2, 0], [2, 3, 0], [3, 2, 0], [3, 3, 0], [3, 4, 0]], 5, 3],
                        expected=2, hidden=True),
            # 긍정 뒤 부정 버스트
            GradingCase(args=[6, [[1, 0, 1], [1, 1, 1], [1, 2, 1], [1, 3, 0], [1, 4, 0],
                                  [1, 5, 0]], 5, 3], expected=1, hidden=True),
            # 매우 큰 window
            GradingCase(args=[3, [[1, 0, 0], [1, 100, 0], [1, 1000, 0]], 100000, 3],
                        expected=1, hidden=True),
            # 모든 고객 부정 < k
            GradingCase(args=[4, [[1, 0, 0], [1, 1, 0], [2, 2, 0], [2, 3, 0]], 100, 3],
                        expected=0, hidden=True),
            # 두 고객 동일 버스트 → 동시 2
            GradingCase(args=[6, [[1, 0, 0], [1, 1, 0], [1, 10, 1], [2, 0, 0], [2, 1, 0],
                                  [2, 10, 1]], 5, 2], expected=2, hidden=True),
            # 초기화 후 열린 구간
            GradingCase(args=[7, [[1, 0, 0], [1, 1, 0], [1, 2, 0], [1, 3, 1], [1, 4, 0],
                                  [1, 5, 0], [1, 6, 0]], 5, 3], expected=1, hidden=True),
            # k=1, 8명 동시
            GradingCase(args=[8, [[c, 0, 0] for c in range(1, 9)], 0, 1],
                        expected=8, hidden=True),
            # 300명 동시
            GradingCase(args=[900, _CR_DENSE300, 5, 3], expected=300, hidden=True),
            # 1500명 동시
            GradingCase(args=[4500, _CR_DENSE1500, 5, 3], expected=1500, hidden=True),
            # 최대 n, 단일 고객 전부 부정
            GradingCase(args=[200000, _CR_ALLNEG200K, 5, 3], expected=1, hidden=True),
            # 대량 동시 (n≈200k, 66666명)
            GradingCase(args=[199998, _CR_MANY200K, 5, 3], expected=66666, hidden=True),
            # 초기화 대량 스트레스 (2000명이 동일 버스트 반복)
            GradingCase(args=[16000, _CR_CHAIN2000, 4, 3], expected=2000, hidden=True),
            # 혼합 시나리오
            GradingCase(args=[12, [[10, 1, 0], [10, 2, 0], [10, 8, 0], [10, 9, 0], [11, 3, 0],
                                   [11, 4, 0], [11, 5, 0], [11, 20, 1], [12, 4, 0], [12, 5, 0],
                                   [12, 6, 0], [13, 100, 1]], 6, 3], expected=2, hidden=True),
        ],
    ),
}


def get_problem(problem_id: str) -> Problem | None:
    return _PROBLEMS.get(problem_id)


def list_problems() -> list[Problem]:
    return list(_PROBLEMS.values())
