"""Position bias: does the judge's pairwise verdict flip when order is swapped?

For each pair we ask the judge twice — (A, B) and (B, A) — and map each verdict
back to the underlying submission. If an unbiased judge prefers the same
submission both times; a flip means ordering alone changed the verdict.
"""

from collections.abc import Sequence

from app.harness.interface import JudgeAdapter
from app.harness.metrics import flip_rate

# stable, order-independent identifiers for the two submissions in a pair
_SUB_A = "sub_a"
_SUB_B = "sub_b"


def _winner_first_order(label: str) -> str | None:
    # shown as (A=sub_a, B=sub_b)
    return {"A": _SUB_A, "B": _SUB_B}.get(label)


def _winner_swapped_order(label: str) -> str | None:
    # shown as (A=sub_b, B=sub_a)
    return {"A": _SUB_B, "B": _SUB_A}.get(label)


async def run_position_bias(adapter: JudgeAdapter, pairs: Sequence[dict]) -> dict:
    """``pairs``: ``[{"problem_index", "flaws_a", "flaws_b"}, ...]``."""
    first_winners: list[str | None] = []
    swapped_winners: list[str | None] = []
    details = []

    for pair in pairs:
        pi, fa, fb = pair["problem_index"], pair["flaws_a"], pair["flaws_b"]
        v1 = await adapter.pairwise(pi, fa, fb)
        v2 = await adapter.pairwise(pi, fb, fa)
        w1 = _winner_first_order(v1)
        w2 = _winner_swapped_order(v2)
        first_winners.append(w1)
        swapped_winners.append(w2)
        details.append(
            {"problem_index": pi, "verdict_ab": v1, "verdict_ba": v2, "flipped": w1 != w2}
        )

    return {
        "n_pairs": len(pairs),
        "flip_rate": flip_rate(first_winners, swapped_winners),
        "details": details,
    }
