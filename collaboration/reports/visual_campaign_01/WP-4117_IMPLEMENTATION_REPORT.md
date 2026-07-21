# WP-4117 Implementation and Validation Report

## Execution gate

The checkout has no configured Git remote, so fetching `main` was impossible. The supplied baseline is `9fbfa33`, merge PR #447 for WP-4116. Repository history and the Campaign 01 matrix confirm merged implementation evidence for WP-4108 through WP-4116; no predecessor gate is missing.

## Deliverable and acceptance mapping

| WP-4117 requirement | Implemented evidence |
|---|---|
| Seven-state canonical-lock lifecycle | Runtime canon, schema enum, state graph and transition tests |
| Human checklist and lock record | `docs/visual_bible/wp4117_human_lock_record_template.md` |
| Machine-readable record and hashes | Canonical-lock v1 schema and `validate_lock_record` |
| Asset completeness/manifest validation | Required role set, present/reserved distinction, path and SHA-256 verification |
| Prompt reproducibility | Canon checklist and mandatory lock gate/status |
| Recognition and physical/facial/wardrobe consistency | Canon acceptance rules and hidden-caption mandatory gate |
| Group compatibility | Mandatory readiness gate preserving final all-resident test |
| Steward authority | Canon, schema conditional, runtime validation and negative tests; automation always returns `may_grant_canonical: false` |
| Versioning/downstream references | Semantic policy, exact-version/hash pinning and change triggers |
| Supersession/rollback | Reciprocal-link validation and explicit forward-history Steward rollback validation |
| Private/restricted governance | Most-restrictive classification, default denial and no-widening rules |
| Evelyn calibration | Honest candidate record with reserved locations, no hashes/approval and five explicit blockers |
| Diagnostics/tests/anti-patterns | Runtime canon sections 7–8 and focused tests |
| Campaign report/registry integration | This report, updated Campaign 01 report and document registry entries |

All deliverables and acceptance criteria are mapped. Rejected and superseded records are terminal and retained; canonical consumers must pin record/version/hash. Validation recommends review eligibility only.

## Unresolved evidence

No final image assets, asset hashes, completed two-workflow prompt receipts, hidden-caption result, group test, tolerated-limitation acceptance, or explicit Steward lock decision was supplied. Evelyn and every other resident therefore remain noncanonical. Reserved paths are not assets and no placeholder evidence satisfies a gate.

## Exact completion status

**WP-4117 implementation complete; Campaign 01 foundation implementation complete; resident canonical locks awaiting real evidence and explicit Steward review.** Campaign 02 may produce candidates but may not call them canonical.

