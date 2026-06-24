# Judge-reliability harness

An **offline** harness that measures whether our LLM-as-a-judge can be trusted.
It is a developer/debugging tool — **not** part of the request path. The live
scoring split (judge does semantic matching only; `scoring.py` computes the
numbers deterministically) is what makes the judge auditable; this harness
quantifies how stable and unbiased that judge actually is.

It depends only on the `JudgeAdapter` protocol (`interface.py`), so any feature
can plug in. `test_design` provides the first adapter
(`app/features/test_design/harness_adapter.py`).

## What it measures

| Analysis | Module | Question it answers | Key metric |
|---|---|---|---|
| **Consistency** | `consistency.py` | Does the judge give the same verdict when re-run? | recall coefficient-of-variation (flag if > 0.15) |
| **Agreement** | `agreement.py` | Does the judge agree with a human gold label? | per-flaw Cohen's κ, recall MAE & Pearson |
| **Position bias** | `bias_position.py` | Does swapping A/B flip the pairwise winner? | flip rate (0 = unbiased) |
| **Self-preference** | `bias_self_pref.py` | Does a judge model inflate its *own* model's answers? | own-author gap − others-author gap |

All statistics live in `metrics.py` and are pure/dependency-free
(`cv`, `mean_std`, `mae`, `pearson_r`, `cohen_kappa`, `flip_rate`).

## Run it

The analyses call the **real** judge LLM, so a run needs `OPENAI_API_KEY`:

```bash
cd backend
OPENAI_API_KEY=sk-... python -m app.harness.runner --mode all --runs 5 --out reports
# modes: consistency | agreement | position | self-pref | all
```

Output: `reports/test_design_<mode>_<stamp>.json` (raw) and `.md` (readable
summary). Read the markdown: high-variance items in `consistency`, low κ / high
MAE in `agreement`, non-zero `flip_rate` in `position_bias`, and a large
`self_preference` per judge all point at where the rubric/prompt needs work.

> `self-pref` issues real calls across **multiple** judge models
> (`fixtures/panel_models.json`) and is the costly, optional part. `consistency`,
> `agreement`, and `position` use the default `settings.llm_model`.

## Fixtures (committed, no key needed to read)

`app/features/test_design/fixtures/`:

- `synthetic_submissions.json` — candidate verification-item submissions, hand-written
  per problem at three quality levels (strong / mediocre / hallucinated). Each item:
  `{key, problem_index, author_model, quality, flaws[]}`.
- `human_gold.json` — the single-annotator gold: `{key, matched_ids[], recall}`. A
  submission that merely restates a `provided_test` is **neutral** (left out of
  `matched_ids`); a wrong/irrelevant item is also not matched.
- `panel_models.json` — judge/author model ids for the self-preference sweep.

`tests/test_harness_fixtures.py` (run with `pytest -m harness`, no key) keeps these
coherent with the live problem set: every key is labeled, every `matched_id` is a
real flaw of that problem, and `recall == len(matched_ids)/len(flaws)`. If a
problem's flaws change, that test fails until the gold is re-labeled.

### Refreshing the synthetic set

```bash
# 1) regenerate submissions with a real LLM (optional; overwrites the fixture)
OPENAI_API_KEY=sk-... python -m app.features.test_design.scripts.gen_synthetic
# 2) hand-label the new keys in human_gold.json (matched_ids + recall)
# 3) verify coherence
pytest -m harness
```

## Plugging in a new feature

1. Implement `JudgeAdapter` (`score()` + `pairwise()`) for the feature, wrapping
   its judge + deterministic scoring — see `test_design/harness_adapter.py`.
2. Add fixtures (synthetic submissions + human gold) under the feature.
3. Register the adapter in `runner.py`.

The four analyses then run against it unchanged.
