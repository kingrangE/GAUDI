"""Fixed, human-authored coding-test problems (seed data).

Each problem is fully specified: the candidate-facing statement + starter stub,
the visible sample cases and hidden grading cases, plus the judge-only
reference solution and rubric. `seed_problems.py` loads these into the DB.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    args: list
    expected: object


@dataclass(frozen=True)
class ProblemSeed:
    id: str
    title: str
    description_md: str
    function_name: str
    starter_code: str
    difficulty: str
    reference_solution: str
    rubric: dict
    comparison: str  # "exact" | "unordered"
    samples: tuple[Case, ...]
    grading: tuple[Case, ...]


_TWO_SUM = ProblemSeed(
    id="two-sum",
    title="두 수의 합",
    description_md=(
        "정수 배열 `nums`와 정수 `target`이 주어집니다. 더해서 `target`이 되는 두 원소의 "
        "**인덱스를 오름차순으로** 반환하세요. 정답은 유일하다고 가정합니다.\n\n"
        "예) `nums=[2,7,11,15], target=9` → `[0, 1]`"
    ),
    function_name="two_sum",
    starter_code=(
        "def two_sum(nums, target):\n"
        "    # TODO: 더해서 target이 되는 두 인덱스를 오름차순으로 반환\n"
        "    pass\n"
    ),
    difficulty="easy",
    reference_solution=(
        "def two_sum(nums, target):\n"
        "    seen = {}\n"
        "    for i, n in enumerate(nums):\n"
        "        if target - n in seen:\n"
        "            return sorted([seen[target - n], i])\n"
        "        seen[n] = i\n"
        "    return []\n"
    ),
    rubric={
        "expected_complexity": "O(n) time, O(n) space (해시맵 1패스)",
        "key_concepts": ["해시맵 보수 탐색", "한 번의 순회", "인덱스 추적"],
        "common_pitfalls": ["O(n^2) 이중 반복", "같은 원소 재사용", "인덱스 정렬 누락"],
    },
    comparison="exact",
    samples=(
        Case([[2, 7, 11, 15], 9], [0, 1]),
        Case([[3, 2, 4], 6], [1, 2]),
    ),
    grading=(
        Case([[2, 7, 11, 15], 9], [0, 1]),
        Case([[3, 2, 4], 6], [1, 2]),
        Case([[3, 3], 6], [0, 1]),
        Case([[1, 5, 3, 8], 11], [2, 3]),
        Case([[0, 4, 3, 0], 0], [0, 3]),
    ),
)


_GROUP_ANAGRAMS = ProblemSeed(
    id="group-anagrams",
    title="애너그램 그룹",
    description_md=(
        "문자열 배열 `strs`가 주어집니다. 서로 애너그램인 문자열끼리 묶어 **그룹들의 리스트**로 "
        "반환하세요. **그룹의 순서와 그룹 내 문자열 순서는 채점에 영향을 주지 않습니다.**\n\n"
        "예) `[\"eat\",\"tea\",\"tan\",\"ate\",\"nat\",\"bat\"]` → "
        "`[[\"eat\",\"tea\",\"ate\"],[\"tan\",\"nat\"],[\"bat\"]]`"
    ),
    function_name="group_anagrams",
    starter_code=(
        "def group_anagrams(strs):\n"
        "    # TODO: 애너그램끼리 묶어 그룹들의 리스트로 반환\n"
        "    pass\n"
    ),
    difficulty="medium",
    reference_solution=(
        "def group_anagrams(strs):\n"
        "    groups = {}\n"
        "    for s in strs:\n"
        "        key = ''.join(sorted(s))\n"
        "        groups.setdefault(key, []).append(s)\n"
        "    return list(groups.values())\n"
    ),
    rubric={
        "expected_complexity": "O(n·k log k) — 각 문자열 정렬을 키로 사용",
        "key_concepts": ["정렬된 문자열 키", "딕셔너리 그룹핑"],
        "common_pitfalls": ["O(n^2) 쌍별 비교", "키 정규화 실패", "빈 문자열 처리 누락"],
    },
    comparison="unordered",
    samples=(
        Case([["eat", "tea", "tan", "ate", "nat", "bat"]],
             [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]),
        Case([[""]], [[""]]),
    ),
    grading=(
        Case([["eat", "tea", "tan", "ate", "nat", "bat"]],
             [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]),
        Case([[""]], [[""]]),
        Case([["a"]], [["a"]]),
        Case([["abc", "bca", "cab", "xyz"]], [["abc", "bca", "cab"], ["xyz"]]),
        Case([["listen", "silent", "hello"]], [["listen", "silent"], ["hello"]]),
    ),
)


_VALID_PARENS = ProblemSeed(
    id="valid-parentheses",
    title="올바른 괄호",
    description_md=(
        "괄호 문자열 `s`(`()[]{}`)가 주어집니다. 모든 괄호가 올바르게 짝지어지고 중첩되면 "
        "`True`, 아니면 `False`를 반환하세요.\n\n"
        "예) `\"()[]{}\"` → `True`, `\"([)]\"` → `False`"
    ),
    function_name="is_valid",
    starter_code=(
        "def is_valid(s):\n"
        "    # TODO: 괄호가 올바르게 짝지어지는지 True/False로 반환\n"
        "    pass\n"
    ),
    difficulty="easy",
    reference_solution=(
        "def is_valid(s):\n"
        "    pairs = {')': '(', ']': '[', '}': '{'}\n"
        "    stack = []\n"
        "    for ch in s:\n"
        "        if ch in '([{':\n"
        "            stack.append(ch)\n"
        "        elif ch in pairs:\n"
        "            if not stack or stack.pop() != pairs[ch]:\n"
        "                return False\n"
        "    return not stack\n"
    ),
    rubric={
        "expected_complexity": "O(n) time, O(n) space (스택)",
        "key_concepts": ["스택 LIFO", "여는/닫는 괄호 매칭"],
        "common_pitfalls": ["빈 스택에서 pop", "끝에 남은 여는 괄호 미검사", "짝 종류 혼동"],
    },
    comparison="exact",
    samples=(
        Case(["()"], True),
        Case(["()[]{}"], True),
        Case(["(]"], False),
    ),
    grading=(
        Case(["()"], True),
        Case(["()[]{}"], True),
        Case(["(]"], False),
        Case(["([)]"], False),
        Case(["{[]}"], True),
        Case([""], True),
    ),
)


PROBLEMS: tuple[ProblemSeed, ...] = (_TWO_SUM, _GROUP_ANAGRAMS, _VALID_PARENS)
