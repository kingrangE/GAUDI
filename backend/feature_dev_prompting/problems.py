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
}


def get_problem(problem_id: str) -> Problem | None:
    return _PROBLEMS.get(problem_id)


def list_problems() -> list[Problem]:
    return list(_PROBLEMS.values())
