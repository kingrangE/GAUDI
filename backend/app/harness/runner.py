"""CLI entrypoint for the offline judge-reliability harness.

Hits a REAL LLM (needs OPENAI_API_KEY) — this is a developer/debugging tool, not
part of the app. It loads test_design's committed fixtures, runs the requested
analyses against the live judge, and writes a JSON+markdown report.

    python -m app.harness.runner --mode all --runs 5 --out reports
"""

import argparse
import asyncio
import json
from datetime import datetime, timezone
from itertools import groupby
from pathlib import Path

from app.features.test_design.harness_adapter import TestDesignAdapter
from app.harness import agreement, bias_position, bias_self_pref, consistency
from app.harness.report import write_report

_FIXTURES = Path(__file__).resolve().parents[1] / "features" / "test_design" / "fixtures"


def _load(name: str):
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _build_pairs(synthetic: list[dict]) -> list[dict]:
    pairs = []
    keyed = sorted(synthetic, key=lambda s: s["problem_index"])
    for pi, group in groupby(keyed, key=lambda s: s["problem_index"]):
        subs = list(group)
        for a, b in zip(subs, subs[1:]):
            pairs.append({"problem_index": pi, "flaws_a": a["flaws"], "flaws_b": b["flaws"]})
    return pairs


async def _run(mode: str, runs: int, out: str) -> None:
    synthetic = _load("synthetic_submissions.json")
    gold_labels = {g["key"]: g for g in _load("human_gold.json")}
    panel = _load("panel_models.json")

    gold = [
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
    items = [{"problem_index": s["problem_index"], "flaws": s["flaws"]} for s in synthetic]
    human_recall_by_key = {k: g["recall"] for k, g in gold_labels.items()}

    default_adapter = TestDesignAdapter()
    results: dict = {}

    if mode in ("consistency", "all"):
        results["consistency"] = await consistency.run_consistency(
            default_adapter, items, runs=runs
        )
    if mode in ("agreement", "all"):
        results["agreement"] = await agreement.run_agreement(default_adapter, gold)
    if mode in ("position", "all"):
        results["position_bias"] = await bias_position.run_position_bias(
            default_adapter, _build_pairs(synthetic)
        )
    if mode in ("self-pref", "all"):
        adapters = {m: TestDesignAdapter(model=m) for m in panel["judge_models"]}
        results["self_preference"] = await bias_self_pref.run_self_preference(
            adapters, synthetic, human_recall_by_key
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path, md_path = write_report(results, out, f"test_design_{mode}", stamp)
    print(f"wrote {json_path}\nwrote {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline judge-reliability harness")
    parser.add_argument(
        "--mode",
        choices=["consistency", "agreement", "position", "self-pref", "all"],
        default="all",
    )
    parser.add_argument("--runs", type=int, default=consistency.DEFAULT_RUNS)
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()
    asyncio.run(_run(args.mode, args.runs, args.out))


if __name__ == "__main__":
    main()
