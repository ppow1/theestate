# PROD-PTM-001A completion receipt

Status: Implementation complete; awaiting Chief Architect review

Completed: 2026-07-16

Gate: PTM-PROD-G1 interface freeze candidate (not accepted or complete)

## Changed seams

- `src/estate/core/ptm_read_only_adapters.py` adds the reusable PTM read-only
  runtime at the existing Estate core seam. It does not add a service, registry,
  queue, scheduler, validator, event ledger, or write-back path.
- `tests/test_ptm_read_only_adapters.py` supplies the bounded production-package
  contract and immutability evidence.

## Gate G1 interface freeze candidate

- Adapter version: `ptm-prod-g1`.
- Pilot adapter names: `parking_lot_source_adapter`,
  `work_package_source_adapter`, `dispatch_source_adapter`,
  `validation_source_adapter`, and `acceptance_source_adapter`.
- The frozen candidate envelope is `AdapterRecord`, containing its immutable
  `SourceReference`, explicit `AdapterState` and `Freshness`, hashes, warnings,
  evidence/reference arrays, confidence, and per-field source provenance.
- Repository-relative, allowlisted paths; regular-file, no-symlink, read-only
  opens; bounded record and byte counts; stable output ordering; and uncertainty
  rather than inference are fail-closed runtime invariants.
- Chief Architect protected review is still required. This receipt does not mark
  Gate G1 complete, merge the change, or authorize projection work.

## Commands and results

| Command | Result |
| --- | --- |
| `pytest -q tests/test_ptm_read_only_adapters.py` | PASS — 4 passed in 0.16s |
| `python -m compileall -q src/estate/core/ptm_read_only_adapters.py tests/test_ptm_read_only_adapters.py` | PASS |
| `git diff --check` | PASS |
| `pytest -q` | FAIL (pre-existing/unrelated OpenWebUI Campaign 02 expectations) — 3 failed, 1344 passed in 141.30s; failures were `test_catalog_exposes_all_residents_with_honest_avatar_and_voice_states`, `test_gateway_response_exposes_identity_trace_metadata`, and `test_validation_writes_reports_and_review_package` in `tests/test_openwebui_campaign_02.py` |

## Acceptance coverage

The targeted tests cover valid, missing, malformed UTF-8, conflicting lifecycle
status, stale, repository-escaping, unallowlisted, oversized, over-count, and
pilot evidence inputs. They also compare normalized results from identical source
snapshots and verify that source content, timestamp, and mode are unchanged after
adapter execution. Every extracted value names its source in `field_provenance`;
unavailable values carry an explicit warning.
