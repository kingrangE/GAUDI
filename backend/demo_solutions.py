"""Reference solutions for the built-in problems (assembly/demo layer, not shipped logic).

Two uses:
  * tests/test_problems_consistency.py runs these to re-verify every problem's expected
    values are correct.
  * main.py's DEMO_SOLVER stub returns these so the live demo grades AC without an LLM key.

These are sample answer keys for demonstration — real evaluation uses the LLM solver.
"""

TAXI_FARE = """\
def solution(n, s, a, b, fares):
    INF = float("inf")
    d = [[INF] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        d[i][i] = 0
    for u, v, w in fares:
        d[u][v] = min(d[u][v], w)
        d[v][u] = min(d[v][u], w)
    for k in range(1, n + 1):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if d[i][k] + d[k][j] < d[i][j]:
                    d[i][j] = d[i][k] + d[k][j]
    return min(d[s][k] + d[k][a] + d[k][b] for k in range(1, n + 1))
"""

MAX_EXPRESSION = """\
import re
from itertools import permutations


def solution(expression):
    tokens = re.findall(r"\\d+|[*+-]", expression)
    ops = {t for t in tokens if t in "*+-"}
    best = 0
    for order in permutations(ops):
        tk = tokens[:]
        for op in order:
            i = 1
            while i < len(tk) - 1:
                if tk[i] == op:
                    tk[i - 1:i + 2] = [str(eval(tk[i - 1] + op + tk[i + 1]))]
                else:
                    i += 1
        best = max(best, abs(int(tk[0])))
    return best
"""

WALL_CHECK = """\
from itertools import permutations


def solution(n, weak, dist):
    length = len(weak)
    weak2 = weak + [w + n for w in weak]
    answer = len(dist) + 1
    for i in range(length):
        for friends in permutations(dist):
            count = 1
            position = weak2[i] + friends[count - 1]
            for j in range(i, i + length):
                if weak2[j] > position:
                    count += 1
                    if count > len(dist):
                        break
                    position = weak2[j] + friends[count - 1]
            answer = min(answer, count)
    return -1 if answer > len(dist) else answer
"""

STEPPING_STONES = """\
from collections import deque


def solution(stones, k):
    dq = deque()
    res = float("inf")
    for i, v in enumerate(stones):
        while dq and stones[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            res = min(res, stones[dq[0]])
    return res
"""

RANKING_SEARCH = """\
from bisect import bisect_left


def solution(info, query):
    db = {}
    for line in info:
        tok = line.split()
        keys, score = tok[:4], int(tok[4])
        for mask in range(16):
            key = ",".join(keys[i] if not (mask >> i) & 1 else "-" for i in range(4))
            db.setdefault(key, []).append(score)
    for key in db:
        db[key].sort()
    res = []
    for q in query:
        tok = q.replace(" and ", " ").split()
        key = ",".join(tok[:4])
        score = int(tok[4])
        arr = db.get(key, [])
        res.append(len(arr) - bisect_left(arr, score))
    return res
"""

CACTUS_HIDE = """\
def solution(m, n, h, w, drops):
    D = len(drops)

    def check(k):
        pref = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(k):
            r, c = drops[i]
            pref[r + 1][c + 1] += 1
        for i in range(1, m + 1):
            row, prev = pref[i], pref[i - 1]
            for j in range(1, n + 1):
                row[j] += row[j - 1] + prev[j] - prev[j - 1]
        for r in range(0, m - h + 1):
            for c in range(0, n - w + 1):
                s = pref[r + h][c + w] - pref[r][c + w] - pref[r + h][c] + pref[r][c]
                if s == 0:
                    return [r, c]
        return None

    lo, hi = 0, D
    best = check(0)
    while lo <= hi:
        mid = (lo + hi) // 2
        res = check(mid)
        if res is not None:
            best = res
            lo = mid + 1
        else:
            hi = mid - 1
    return best
"""

CHURN_RISK_STREAM = """\
from collections import defaultdict


def solution(n, events, window, k):
    by_cust = defaultdict(list)
    for cid, ts, typ in events:
        by_cust[cid].append((ts, typ))

    deltas = defaultdict(int)  # coord -> net change to the running at-risk count
    for evs in by_cust.values():
        evs.sort()  # (ts, type): ts asc, negative(0) before positive(1) on ties
        neg = []            # negative timestamps in the current segment (since last reset)
        left = 0            # two-pointer left bound into neg
        at_risk = False
        enter = None
        for ts, typ in evs:
            if typ == 1:  # positive -> end at-risk + reset negative history
                if at_risk:
                    deltas[enter] += 1
                    deltas[ts] -= 1
                    at_risk = False
                    enter = None
                neg = []
                left = 0
            else:  # negative
                neg.append(ts)
                if not at_risk:
                    while neg[left] < ts - window:
                        left += 1
                    if len(neg) - left >= k:
                        at_risk = True
                        enter = ts
        if at_risk:  # never reset -> open-ended [enter, +inf)
            deltas[enter] += 1

    ans = 0
    running = 0
    for coord in sorted(deltas):
        running += deltas[coord]
        if running > ans:
            ans = running
    return ans
"""

# problem id -> reference solution code
REFERENCE: dict[str, str] = {
    "taxi-fare": TAXI_FARE,
    "max-expression": MAX_EXPRESSION,
    "wall-check": WALL_CHECK,
    "stepping-stones": STEPPING_STONES,
    "ranking-search": RANKING_SEARCH,
    "cactus-hide": CACTUS_HIDE,
    "churn-risk-stream": CHURN_RISK_STREAM,
}

# unique phrase in each statement, used by the demo stub to pick the matching solution
DETECT: dict[str, str] = {
    "taxi-fare": "합승",
    "max-expression": "수식",
    "wall-check": "외벽",
    "stepping-stones": "징검다리",
    "ranking-search": "지원자",
    "cactus-hide": "선인장",
    "churn-risk-stream": "이탈 위험",
}
