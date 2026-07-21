# WP-4118 Implementation and Validation Report

**Implementation status:** Complete
**Portrait production status:** Not started for all commissioned residents
**Steward approvals claimed:** None

## Execution gate

The implementation baseline is merge commit `7583df2`, the merged WP-4117 pull request. Campaign
01's completion report maps WP-4108 through WP-4117 and explicitly authorizes Campaign 02 to begin
with candidate manifests. WP-4117's completion receipt records zero resident canonical approvals.
All WP-4118 declared dependencies are therefore present and implementation-complete; outstanding
human image review is intentionally not confused with foundation completeness.

## Deliverable and acceptance mapping

| Requirement | Evidence |
| --- | --- |
| Runtime canon, hierarchy, alternates, promotion | `docs/visual_bible/wp4118_hero_portrait_runtime_canon.md` §§1–2 |
| Composition, identity, adult, wardrobe, expression/role | Runtime canon §3 |
| Masters, derivatives, square/4:5/16:9 safety | Runtime canon §4; metadata schema |
| Candidate sets and selection rationale | Runtime canon §5; comparison and review templates |
| Metadata, provenance, hashes | Runtime canon §6; hero metadata sidecar schema |
| States and deterministic directories | Runtime canon §§2, 7; resident trees and hero manifests |
| Checklist and anti-patterns | Production checklist; runtime canon §8 |
| Missing metadata validation | `test_missing_metadata_sidecar_is_rejected` |
| Duplicate canon validation | `test_duplicate_canonical_hero_declarations_are_rejected` |
| Stale hash validation | `test_stale_asset_hash_is_rejected` |
| Unapproved promotion validation | `test_unapproved_canonical_promotion_is_rejected` |
| Exactly one governed hero slot | Validator canonical uniqueness and locked-state checks |
| Small-crop identity protection | Safe-area contract and review form |
| Generic convergence prevention | Runtime canon §§3, 8; production/review checks |
| Reproducible/auditable provenance | Sidecar required provenance and hash validation |
| Single-window comparison | Comparison-sheet template with three consistently labeled columns |
| Honest sample | Evelyn pending-production note; no image bytes or false evidence |
| Every commissioned resident state | Catalog coverage check against active resident registry; eight `not_started` hero manifests |

## Files and systems

- Authoritative runtime canon and authoring templates.
- Versioned hero sidecar and resident hero-manifest schemas.
- Catalog-integrated manifests and complete directory convention for every active resident.
- Validator CLI enforcing registry coverage, paths, lifecycle, metadata, hashes, review gates, and
  explicit matching Steward promotion evidence.
- Focused positive and failure-path tests.

## Honest resident status summary

| Resident | Manifest state | Evidence state |
| --- | --- | --- |
| Alfred | `not_started` | No candidates, review, approval, or lock |
| Ingrid | `not_started` | No candidates, review, approval, or lock |
| Helen | `not_started` | No candidates, review, approval, or lock |
| Eleanor | `not_started` | No candidates, review, approval, or lock |
| Marie | `not_started` | No candidates, review, approval, or lock |
| Judy | `not_started` | No candidates, review, approval, or lock |
| Evelyn | `not_started` | Text-only pending-production sample; no image |
| Grace | `not_started` | No candidates, review, approval, or lock |

## Limitations and next action

No approved generator output or local Steward decision was supplied. No generated images, comparison
results, completed reviews, approvals, or canonical hashes are claimed. Next, an authorized production
workflow may create three sidecar-complete candidates for one resident, validate them, and submit the
comparison set to the Steward. WP-4119 must preserve this canon rather than infer an image state.

## Validation record

- `PYTHONPATH=src python -m estate.portraits.validator --root .` — passed (one benign Python module
  re-import warning was emitted by `runpy`).
- `PYTHONPATH=src pytest -q tests/test_portrait_campaign_02.py tests/test_wp4118_hero_portrait.py`
  — 11 passed.
- `PYTHONPATH=src pytest -q` — 1718 passed, 5 skipped, and 7 pre-existing unrelated failures in
  conversation decoding/recovery, notification snoozing, Open WebUI identity/voice states, and a
  reconstructed handoff terminator. The WP-4118 focused suites passed within the same run.
