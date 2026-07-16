# PROD-PTM-001C completion receipt

Status: Implementation complete; awaiting Chief Architect merge review

Completed: 2026-07-16

Gate: PTM-PROD-G2 remains pending

## Implementation completion

- `src/estate/core/ptm_pilot_projection.py` implements the bounded, ephemeral
  projection over one portfolio, five Parking Lot items, two work packages, one
  Dispatch evidence chain, one validation result, and one acceptance reference.
- The projection consumes only the frozen `ptm-prod-g1` adapter envelopes. It
  does not read source bodies directly, persist output, create a canonical event
  log, mutate a source, dispatch work, infer acceptance, or add a service.
- `estate ptm-pilot-projection --format json|report` uses the existing Estate CLI
  command surface. JSON is normalized and byte-stable; the report contains only
  bounded metadata, source paths, SHA-256 hashes, state, freshness, metrics, and
  warnings. Extracted titles and source payloads are intentionally excluded.
- Cycle time and blocked duration remain explicitly unknown because the frozen
  adapter does not expose authoritative intervals. Audit completeness is the
  only calculated metric and requires an available, current, hashed,
  field-provenanced record without adapter warnings.

## Validation evidence

Targeted tests cover repeated byte-equivalent rebuilds, field-level provenance,
warning coverage, exact pilot cardinality, missing sources, stale sources,
conflicting sources, private-payload exclusion, normalized JSON, reviewer report
rendering, and write-rejecting instrumentation. The existing adapter tests retain
the repository containment, allowlist, bounded-read, malformed-input, and source
immutability evidence.

## Commands and results

| Command | Result |
| --- | --- |
| `pytest -q tests/test_ptm_read_only_adapters.py tests/test_ptm_pilot_projection.py` | PASS — 9 passed |
| `PYTHONPATH=src python -m estate.cli.main ptm-pilot-projection --format json` (twice) followed by `cmp` and `python -m json.tool` | PASS — repeated output byte-equivalent and valid JSON |
| `PYTHONPATH=src python -m estate.cli.main ptm-pilot-projection --format report` | PASS — reviewer report emitted with 11 source references/hashes and explicit warnings |
| `python -m compileall -q src/estate/core/ptm_pilot_projection.py tests/test_ptm_pilot_projection.py` | PASS |
| `pytest -q` | PASS |
| `git diff --check` | PASS |

## Decision boundaries

- **Implementation completion:** recorded by this receipt.
- **Merge review:** not complete; the Chief Architect must review the PR.
- **Gate G2 decision:** pending. `PROD-PTM-001B` must be integrated first and
  all campaign evidence reviewed.
- **Institutional acceptance:** not requested, inferred, or granted by this
  implementation, its tests, this receipt, or a future merge.

No source mutation, Phase 2 ledger, workspace UI, dispatch action, rollout, or
acceptance inference is delivered.
