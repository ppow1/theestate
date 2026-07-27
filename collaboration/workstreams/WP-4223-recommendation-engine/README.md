# WP-4223 Engineering Campaign Recommendation Engine

This isolated package produces **advisory, deterministic recommendations only**. It does not
schedule, assign, dispatch, mutate lifecycle/WIP/Parking Lot records, write provider artifacts,
or invoke Git. The repository already contains an earlier WP-4223 operator-surface package;
therefore this assignment is isolated in the explicitly named `WP-4223-recommendation-engine`
boundary rather than overwriting that authoritative artifact.

## Inputs and reuse

The engine consumes the WP-4222 `estate.engineering-dashboard-integration/v1` envelope. That
envelope contains the WP-4221 snapshot projected from the WP-4220 queue. With `--manifest`, the
CLI calls WP-4222's existing registry/composition directly. It never re-discovers providers.
WP-4214 duration values are looked up only from an optional published provider payload; WP-4215
parallel safety and WP-4217 Git readiness remain queue references/classifications. Missing
optional evidence degrades scoring or eligibility and is never invented.

## Deterministic policy

Every row receives an integer score: authoritative queue priority, `12` per direct dependent,
`+25` ready, `+20` validation, `+15` when a published duration is at most eight hours, `+8`
low merge risk, `-15` high merge risk, `-10` per blocker, `-30` stale, `-100` superseded,
`-5` missing Git readiness, and `-5` missing evidence. Categories use explicit field predicates
in `engine.py`; sorting is score descending, identifier ascending. Parallel recommendations
only combine queue-declared safe members sharing a group. The source integration hash, queue
generation, item evidence, provider status, score terms, and policy version make every result
explainable. No clock, random value, filesystem discovery, model output, or network input is used.

## CLI

```bash
python collaboration/workstreams/WP-4223-recommendation-engine/recommend.py validate INPUT.json
python collaboration/workstreams/WP-4223-recommendation-engine/recommend.py recommend INPUT.json --limit 10
python collaboration/workstreams/WP-4223-recommendation-engine/recommend.py explain INPUT.json CATEGORY:ITEM
python collaboration/workstreams/WP-4223-recommendation-engine/recommend.py compare INPUT.json CATEGORY:ITEM_A CATEGORY:ITEM_B
python collaboration/workstreams/WP-4223-recommendation-engine/recommend.py recommend \
  collaboration/workstreams/WP-4222/fixtures/providers.json --manifest
```

`compare` reports the mechanical ordering and score delta; it does not choose or authorize work.
All commands write JSON to stdout only. Exit status `2` indicates malformed or incompatible input.

## Contents and removal

* `recommendation_engine/`: pure validation, scoring, categorization, explanation, and comparison.
* `schemas/`: input and output JSON Schema contracts.
* `fixtures/`: eight representative campaign scenarios.
* `tests/`: focused determinism, degradation, validation, tie-break, provenance, and CLI tests.
* `examples/`: reproducible result composed through WP-4222.

Removal is deletion of this directory. There is no migration or authoritative-state cleanup.
