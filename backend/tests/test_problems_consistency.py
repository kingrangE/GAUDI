"""Validate that every registered problem's expected values are self-consistent:
each problem's reference solution must pass all of its own cases (public + hidden).
This catches hand-authored expected-value mistakes in the registry.
"""

import demo_solutions
from feature_dev_prompting.problems import list_problems
from feature_dev_prompting.sandbox import run_against_tests


def test_every_problem_passes_its_reference_solution():
    for problem in list_problems():
        assert problem.id in demo_solutions.REFERENCE, f"no reference for {problem.id}"
        code = demo_solutions.REFERENCE[problem.id]
        results = run_against_tests(code, problem.tests, problem.entry_point, time_limit=10.0)
        failed = [(r.index, r.status) for r in results if not r.passed]
        assert not failed, f"{problem.id} reference failed cases: {failed}"


def test_every_problem_has_public_and_hidden_cases():
    for problem in list_problems():
        kinds = {t.hidden for t in problem.tests}
        assert kinds == {True, False}, f"{problem.id} must have both public and hidden cases"


def test_demo_detect_phrases_match_statements():
    # the demo stub picks a solution by finding DETECT[id] in the prompt (statement)
    for problem in list_problems():
        phrase = demo_solutions.DETECT.get(problem.id)
        assert phrase and phrase in problem.statement, f"{problem.id} statement missing phrase"
