"""CLI entrypoint for the offline cs_eval judge-reliability harness.

Hits a REAL LLM (needs OPENAI_API_KEY) — a developer/debugging tool, not part of
the app. Loads the committed human-gold fixture, runs the cs_eval-native
analyses against the live judge, and writes a JSON+markdown report via the
shared ``app.harness.report``. Mirrors ``app.harness.runner`` (test_design).

    python -m app.features.cs_eval.harness_runner --mode all --runs 5 --out reports
"""

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.features.cs_eval import harness_eval
from app.features.cs_eval.harness_adapter import CsEvalAdapter
from app.harness.report import write_report

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str):
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


async def _run(mode: str, runs: int, out: str) -> None:
    gold = _load("cs_gold.json")
    items = [
        {"question_index": g["question_index"], "answer_text": g["answer_text"]}
        for g in gold
    ]

    adapter = CsEvalAdapter()
    results: dict = {}

    if mode in ("agreement", "all"):
        results["agreement"] = await harness_eval.run_agreement(adapter, gold)
    if mode in ("consistency", "all"):
        results["consistency"] = await harness_eval.run_consistency(
            adapter, items, runs=runs
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path, md_path = write_report(results, out, f"cs_eval_{mode}", stamp)
    print(f"wrote {json_path}\nwrote {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline cs_eval judge-reliability harness")
    parser.add_argument(
        "--mode", choices=["agreement", "consistency", "all"], default="all"
    )
    parser.add_argument("--runs", type=int, default=harness_eval.DEFAULT_RUNS)
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()
    asyncio.run(_run(args.mode, args.runs, args.out))


if __name__ == "__main__":
    main()
