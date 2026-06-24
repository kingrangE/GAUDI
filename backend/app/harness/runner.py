"""CLI entrypoint for the offline judge-reliability harness.

Hits a REAL LLM (needs OPENAI_API_KEY) — this is a developer/debugging tool, not part of
the app. It loads a feature's committed fixtures, runs the requested analyses against that
feature's live judge (via its ``JudgeAdapter``), and writes a JSON+markdown report.

The runner is feature-agnostic: ``--feature`` selects any target registered in
``app.harness.registry`` (test_design is registered below). A feature becomes pluggable as
soon as it ships a ``JudgeAdapter`` and the standard fixture set
(``synthetic_submissions.json`` / ``human_gold.json`` / ``panel_models.json``) — no change to
the analyses or this CLI is needed.

    python -m app.harness.runner --feature test_design --mode all --runs 5 --out reports
    python -m app.harness.runner --list
"""

import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import groupby
from pathlib import Path

from app.features.test_design.harness_adapter import TestDesignAdapter
from app.harness import agreement, bias_position, bias_self_pref, consistency
from app.harness.registry import HarnessTarget, get_target, list_targets, register_target
from app.harness.report import write_report


@dataclass
class Fixtures:
    """The standard fixture set every harness target ships."""

    synthetic: list[dict]
    gold_labels: dict[str, dict]
    panel: dict


def load_fixtures(fixtures_dir: Path) -> Fixtures:
    """Load the three standard fixture files from a target's directory."""

    def _load(name: str):
        return json.loads((fixtures_dir / name).read_text(encoding="utf-8"))

    return Fixtures(
        synthetic=_load("synthetic_submissions.json"),
        gold_labels={g["key"]: g for g in _load("human_gold.json")},
        panel=_load("panel_models.json"),
    )


def _build_pairs(synthetic: list[dict]) -> list[dict]:
    pairs = []
    keyed = sorted(synthetic, key=lambda s: s["problem_index"])
    for pi, group in groupby(keyed, key=lambda s: s["problem_index"]):
        subs = list(group)
        for a, b in zip(subs, subs[1:]):
            pairs.append({"problem_index": pi, "flaws_a": a["flaws"], "flaws_b": b["flaws"]})
    return pairs


async def run_analyses(target: HarnessTarget, fx: Fixtures, mode: str, runs: int) -> dict:
    """Run the requested reliability analyses for ``target`` against its fixtures.

    Pure orchestration — no disk, no argv — so it is unit-testable with a stub adapter.
    """

    gold = [
        {
            "problem_index": s["problem_index"],
            "flaws": s["flaws"],
            "human": {
                "matched_ids": fx.gold_labels[s["key"]]["matched_ids"],
                "recall": fx.gold_labels[s["key"]]["recall"],
            },
        }
        for s in fx.synthetic
        if s["key"] in fx.gold_labels
    ]
    items = [{"problem_index": s["problem_index"], "flaws": s["flaws"]} for s in fx.synthetic]
    human_recall_by_key = {k: g["recall"] for k, g in fx.gold_labels.items()}

    default_adapter = target.make_adapter(None)
    results: dict = {}

    if mode in ("consistency", "all"):
        results["consistency"] = await consistency.run_consistency(
            default_adapter, items, runs=runs
        )
    if mode in ("agreement", "all"):
        results["agreement"] = await agreement.run_agreement(default_adapter, gold)
    if mode in ("position", "all"):
        results["position_bias"] = await bias_position.run_position_bias(
            default_adapter, _build_pairs(fx.synthetic)
        )
    if mode in ("self-pref", "all"):
        adapters = {m: target.make_adapter(m) for m in fx.panel["judge_models"]}
        results["self_preference"] = await bias_self_pref.run_self_preference(
            adapters, fx.synthetic, human_recall_by_key
        )
    return results


async def _run(feature: str, mode: str, runs: int, out: str) -> None:
    target = get_target(feature)
    fx = load_fixtures(target.fixtures_dir)
    results = await run_analyses(target, fx, mode, runs)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path, md_path = write_report(results, out, f"{feature}_{mode}", stamp)
    print(f"wrote {json_path}\nwrote {md_path}")


# Built-in targets. A new feature registers itself here (or from its own module) once it ships
# an adapter + fixtures — the analyses and the CLI stay untouched.
_TEST_DESIGN_FIXTURES = (
    Path(__file__).resolve().parents[1] / "features" / "test_design" / "fixtures"
)
register_target(
    HarnessTarget(
        name="test_design",
        make_adapter=lambda model: TestDesignAdapter(model=model),
        fixtures_dir=_TEST_DESIGN_FIXTURES,
    )
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline judge-reliability harness")
    parser.add_argument("--feature", default="test_design", help="registered harness target")
    parser.add_argument(
        "--mode",
        choices=["consistency", "agreement", "position", "self-pref", "all"],
        default="all",
    )
    parser.add_argument("--runs", type=int, default=consistency.DEFAULT_RUNS)
    parser.add_argument("--out", default="reports")
    parser.add_argument("--list", action="store_true", help="list registered targets and exit")
    args = parser.parse_args()
    if args.list:
        print("\n".join(list_targets()))
        return
    asyncio.run(_run(args.feature, args.mode, args.runs, args.out))


if __name__ == "__main__":
    main()
