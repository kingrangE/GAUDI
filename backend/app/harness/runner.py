"""CLI entrypoint for the offline judge-reliability harness.

Hits a REAL LLM (needs OPENAI_API_KEY) — this is a developer/debugging tool, not part of
the app. It loads a feature's committed fixtures, runs the requested analyses against that
feature's live judge (via its ``JudgeAdapter``), and writes a JSON+markdown report.

The runner is feature-agnostic: ``--feature`` selects any target registered in
``app.harness.registry``. A feature becomes pluggable as soon as it ships a ``JudgeAdapter``
and either the standard fixture set
(``synthetic_submissions.json`` / ``human_gold.json`` / ``panel_models.json``, keyed by
submission ``key``) or its own ``build_inputs`` shaper when its judge needs differently shaped
inputs (e.g. rejection_eval's per-problem classifier) — the analyses and this CLI stay
untouched either way.

    python -m app.harness.runner --feature test_design --mode all --runs 5 --out reports
    python -m app.harness.runner --feature rejection_eval --mode all
    python -m app.harness.runner --list
"""

import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import groupby
from pathlib import Path

from app.features.rejection_eval import harness_adapter as rejection_harness
from app.features.test_design.harness_adapter import TestDesignAdapter
from app.harness import agreement, bias_position, bias_self_pref, consistency
from app.harness.registry import HarnessTarget, get_target, list_targets, register_target
from app.harness.report import write_report
from feature_context_engineering.harness_adapter import ContextEngAdapter


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


def _standard_inputs(fx: Fixtures) -> dict:
    """Shape the standard fixture set into the per-analysis inputs.

    Used by features whose judge matches per-submission flaws against a gold keyed by the
    submission ``key`` (test_design / context_engineering).
    """

    agreement_gold = [
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
    return {
        "consistency_items": [
            {"problem_index": s["problem_index"], "flaws": s["flaws"]} for s in fx.synthetic
        ],
        "agreement_gold": agreement_gold,
        "pairwise_pairs": _build_pairs(fx.synthetic),
        "synthetic": fx.synthetic,
        "human_recall_by_key": {k: g["recall"] for k, g in fx.gold_labels.items()},
        "panel": fx.panel,
    }


async def _analyze(make_adapter, inputs: dict, mode: str, runs: int) -> dict:
    """Run the requested reliability analyses against shaped ``inputs``.

    Pure orchestration — no disk, no argv — so it is unit-testable with a stub adapter.
    """

    default_adapter = make_adapter(None)
    results: dict = {}

    if mode in ("consistency", "all"):
        results["consistency"] = await consistency.run_consistency(
            default_adapter, inputs["consistency_items"], runs=runs
        )
    if mode in ("agreement", "all"):
        results["agreement"] = await agreement.run_agreement(
            default_adapter, inputs["agreement_gold"]
        )
    if mode in ("position", "all"):
        results["position_bias"] = await bias_position.run_position_bias(
            default_adapter, inputs["pairwise_pairs"]
        )
    if mode in ("self-pref", "all"):
        adapters = {m: make_adapter(m) for m in inputs["panel"]["judge_models"]}
        results["self_preference"] = await bias_self_pref.run_self_preference(
            adapters, inputs["synthetic"], inputs["human_recall_by_key"]
        )
    return results


async def run_analyses(target: HarnessTarget, fx: Fixtures, mode: str, runs: int) -> dict:
    """Run the reliability analyses for a standard-fixture ``target`` against its fixtures."""

    return await _analyze(target.make_adapter, _standard_inputs(fx), mode, runs)


async def _run(feature: str, mode: str, runs: int, out: str) -> None:
    target = get_target(feature)
    if target.build_inputs is not None:
        # Feature ships its own inputs shaper (its judge doesn't fit the standard fixtures).
        results = await _analyze(target.make_adapter, target.build_inputs(), mode, runs)
    else:
        fx = load_fixtures(target.fixtures_dir)
        results = await run_analyses(target, fx, mode, runs)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path, md_path = write_report(results, out, f"{feature}_{mode}", stamp)
    print(f"wrote {json_path}\nwrote {md_path}")


# Built-in targets. A new feature registers itself here (or from its own module) once it ships
# an adapter + fixtures — the analyses and the CLI stay untouched.
_FEATURES_DIR = Path(__file__).resolve().parents[1] / "features"

register_target(
    HarnessTarget(
        name="test_design",
        make_adapter=lambda model: TestDesignAdapter(model=model),
        fixtures_dir=_FEATURES_DIR / "test_design" / "fixtures",
    )
)

register_target(
    HarnessTarget(
        name="rejection_eval",
        make_adapter=lambda model: rejection_harness.RejectionEvalAdapter(model=model),
        fixtures_dir=_FEATURES_DIR / "rejection_eval" / "fixtures",
        build_inputs=rejection_harness.build_inputs,
    )
)

register_target(
    HarnessTarget(
        name="context_engineering",
        make_adapter=lambda model: ContextEngAdapter(model),
        fixtures_dir=Path(__file__).resolve().parents[2]
        / "feature_context_engineering"
        / "fixtures",
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
