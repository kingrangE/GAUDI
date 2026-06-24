"""CLI entrypoint for the offline judge-reliability harness.

Hits a REAL LLM (needs OPENAI_API_KEY) — this is a developer/debugging tool, not
part of the app. It loads a feature's committed fixtures, runs the requested
analyses against the live judge, and writes a JSON+markdown report.

    python -m app.harness.runner --feature test_design --mode all --runs 5 --out reports
    python -m app.harness.runner --feature rejection_eval --mode all

Each feature provides an adapter (implementing ``JudgeAdapter``) and a set of
analysis inputs; the analyses themselves are feature-agnostic.
"""

import argparse
import asyncio
import json
from datetime import datetime, timezone
from itertools import groupby
from pathlib import Path

from app.features.rejection_eval import harness_adapter as rejection_harness
from app.features.test_design.harness_adapter import TestDesignAdapter
from app.harness import agreement, bias_position, bias_self_pref, consistency
from app.harness.report import write_report

_TD_FIXTURES = Path(__file__).resolve().parents[1] / "features" / "test_design" / "fixtures"


def _td_load(name: str):
    return json.loads((_TD_FIXTURES / name).read_text(encoding="utf-8"))


def _td_build_pairs(synthetic: list[dict]) -> list[dict]:
    pairs = []
    keyed = sorted(synthetic, key=lambda s: s["problem_index"])
    for pi, group in groupby(keyed, key=lambda s: s["problem_index"]):
        subs = list(group)
        for a, b in zip(subs, subs[1:]):
            pairs.append({"problem_index": pi, "flaws_a": a["flaws"], "flaws_b": b["flaws"]})
    return pairs


def _test_design_inputs() -> dict:
    """test_design's fixtures, shaped into the analysis inputs."""
    synthetic = _td_load("synthetic_submissions.json")
    gold_labels = {g["key"]: g for g in _td_load("human_gold.json")}
    panel = _td_load("panel_models.json")

    agreement_gold = [
        {
            "problem_index": s["problem_index"],
            "flaws": s["flaws"],
            "human": {
                "matched_ids": gold_labels[s["key"]]["matched_ids"],
                "recall": gold_labels[s["key"]]["recall"],
            },
        }
        for s in synthetic
        if s["key"] in gold_labels
    ]
    consistency_items = [
        {"problem_index": s["problem_index"], "flaws": s["flaws"]} for s in synthetic
    ]
    human_recall_by_key = {k: g["recall"] for k, g in gold_labels.items()}
    return {
        "consistency_items": consistency_items,
        "agreement_gold": agreement_gold,
        "pairwise_pairs": _td_build_pairs(synthetic),
        "synthetic": synthetic,
        "human_recall_by_key": human_recall_by_key,
        "panel": panel,
    }


# feature -> (adapter factory, inputs builder)
_FEATURES = {
    "test_design": (TestDesignAdapter, _test_design_inputs),
    "rejection_eval": (rejection_harness.RejectionEvalAdapter, rejection_harness.build_inputs),
}


async def _run(feature: str, mode: str, runs: int, out: str) -> None:
    adapter_factory, build_inputs = _FEATURES[feature]
    inputs = build_inputs()
    default_adapter = adapter_factory()
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
        adapters = {m: adapter_factory(model=m) for m in inputs["panel"]["judge_models"]}
        results["self_preference"] = await bias_self_pref.run_self_preference(
            adapters, inputs["synthetic"], inputs["human_recall_by_key"]
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path, md_path = write_report(results, out, f"{feature}_{mode}", stamp)
    print(f"wrote {json_path}\nwrote {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline judge-reliability harness")
    parser.add_argument("--feature", choices=sorted(_FEATURES), default="test_design")
    parser.add_argument(
        "--mode",
        choices=["consistency", "agreement", "position", "self-pref", "all"],
        default="all",
    )
    parser.add_argument("--runs", type=int, default=consistency.DEFAULT_RUNS)
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()
    asyncio.run(_run(args.feature, args.mode, args.runs, args.out))


if __name__ == "__main__":
    main()
