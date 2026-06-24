"""Tests for the Platinum-tier `churn-risk-stream` problem (이탈 위험 최대 동시 인원).

Guards the authored problem's integrity: it loads, ships exactly 40 cases (public +
hidden), its reference solution passes every case in the real sandbox, and every small
case's stored `expected` is independently reproduced by a naive brute-force oracle.
"""

from collections import defaultdict

import demo_solutions
from feature_dev_prompting.problems import get_problem
from feature_dev_prompting.sandbox import run_against_tests

PROBLEM_ID = "churn-risk-stream"


# ───────────────────────── independent brute-force oracle ─────────────────────────
def _first_enter_naive(neg_ts, window, k):
    """Earliest neg_ts[i] with >= k negatives in the closed window [ts-window, ts]."""
    for i in range(len(neg_ts)):
        lo = neg_ts[i] - window
        hi = neg_ts[i]
        if sum(1 for x in neg_ts if lo <= x <= hi) >= k:
            return neg_ts[i]
    return None


def brute(n, events, window, k):
    """Simple O(n^2)-ish simulation, fully independent of the reference's two-pointer
    + sweepline. Same documented semantics: per-customer (ts, type) order, positive
    resets the negative history, half-open at-risk interval [enter, leave)."""
    by_cust = defaultdict(list)
    for cid, ts, typ in events:
        by_cust[cid].append((ts, typ))

    episodes = []  # (enter, leave_or_None)
    for evs in by_cust.values():
        evs.sort()  # ts asc, negative(0) before positive(1) on ties
        seg = []
        for ts, typ in evs:
            if typ == 1:  # positive terminates the current negative segment
                e = _first_enter_naive(seg, window, k)
                if e is not None:
                    episodes.append((e, ts))
                seg = []
            else:
                seg.append(ts)
        e = _first_enter_naive(seg, window, k)  # trailing, never-terminated segment
        if e is not None:
            episodes.append((e, None))

    if not episodes:
        return 0
    best = 0
    for t in {a for a, _ in episodes}:  # max overlap is attained at some enter instant
        c = sum(1 for (a, b) in episodes if a <= t and (b is None or t < b))
        best = max(best, c)
    return best


def _small_enough(events):
    """Brute is cheap when no customer has a long negative run and few customers."""
    negruns = defaultdict(int)
    custs = set()
    for cid, ts, typ in events:
        custs.add(cid)
        if typ == 0:
            negruns[cid] += 1
    longest = max(negruns.values()) if negruns else 0
    return longest <= 1500 and len(custs) <= 2000


# ───────────────────────────────── tests ─────────────────────────────────
def test_problem_loads():
    p = get_problem(PROBLEM_ID)
    assert p is not None
    assert p.id == PROBLEM_ID
    assert p.entry_point == "solution"
    assert "def solution(n, events, window, k)" in p.starter_code
    assert "이탈 위험" in p.statement  # theme + demo detect phrase


def test_exactly_40_cases_public_and_hidden():
    p = get_problem(PROBLEM_ID)
    assert len(p.tests) == 40
    public = [t for t in p.tests if not t.hidden]
    hidden = [t for t in p.tests if t.hidden]
    assert len(public) == 4
    assert len(hidden) == 36
    assert {t.hidden for t in p.tests} == {True, False}


def test_n_equals_events_length_for_every_case():
    p = get_problem(PROBLEM_ID)
    for i, t in enumerate(p.tests):
        n, events = t.args[0], t.args[1]
        assert n == len(events), f"case {i}: n={n} != len(events)={len(events)}"


def test_reference_solution_passes_all_40_in_sandbox():
    p = get_problem(PROBLEM_ID)
    code = demo_solutions.REFERENCE[PROBLEM_ID]
    results = run_against_tests(code, p.tests, p.entry_point, time_limit=p.time_limit_sec)
    failed = [(r.index, r.status) for r in results if not r.passed]
    assert not failed, f"reference failed cases: {failed}"
    assert sum(r.passed for r in results) == 40


def test_brute_force_agrees_with_stored_expecteds_on_small_cases():
    p = get_problem(PROBLEM_ID)
    checked = 0
    for i, t in enumerate(p.tests):
        n, events, window, k = t.args
        if not _small_enough(events):
            continue
        assert brute(n, events, window, k) == t.expected, f"brute != expected at case {i}"
        checked += 1
    # the vast majority of cases (everything except the two ~200k stress cases) is covered
    assert checked >= 36


def test_brute_matches_reference_on_worked_example():
    # the statement's worked example: window=5, k=3 -> 3 simultaneously at-risk
    events = [
        [1, 0, 0], [1, 2, 0], [1, 3, 0],
        [2, 4, 0], [2, 5, 0], [2, 6, 0], [2, 12, 1],
        [3, 0, 0], [3, 1, 0], [3, 5, 1], [3, 6, 0], [3, 7, 0], [3, 8, 0],
    ]
    assert brute(len(events), events, 5, 3) == 3
    code = demo_solutions.REFERENCE[PROBLEM_ID]
    results = run_against_tests(
        code,
        [get_problem(PROBLEM_ID).tests[0]],  # case 0 is this worked example, expected 3
        "solution",
        time_limit=5.0,
    )
    assert results[0].passed and results[0].status == "pass"


def test_semantics_edge_cases_via_brute():
    # same-ts positive cancels the triggering negative (half-open [t, t) is empty)
    assert brute(4, [[1, 0, 0], [1, 1, 0], [1, 2, 0], [1, 2, 1]], 5, 3) == 0
    # window boundary is inclusive: span == window enters, span == window+1 does not
    assert brute(3, [[1, 0, 0], [1, 4, 0], [1, 8, 0]], 8, 3) == 1
    assert brute(3, [[1, 0, 0], [1, 4, 0], [1, 9, 0]], 8, 3) == 0
    # a positive resets the negative history -> needs k fresh negatives afterwards
    assert brute(4, [[1, 0, 0], [1, 1, 0], [1, 2, 1], [1, 3, 0]], 5, 3) == 0
