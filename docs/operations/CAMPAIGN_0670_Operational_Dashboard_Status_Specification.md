# CAMPAIGN-0670 Operational Dashboard / Status Specification

Status: read-only Gate C specification; not campaign acceptance  
Campaign owner: Chief Architect

## Header and freshness

Display literal campaign ID/title, definition path/digest, parent authority, architecture/acceptance owner, projection version, source high-watermark, `observed_at` in UTC, stale policy, and a prominent `READ-ONLY DERIVED VIEW` label. Any conflict produces a red fail-closed banner and disables/suppresses “next authorized action.”

## Required panels

1. **Campaign and integration gates:** explicit gate decision reference/actor/time; never infer release from package counts.
2. **Package matrix:** IDs; lifecycle; owner/office; lane/provider; readiness/dependencies; branch/PR/integration; validation and acceptance; blocker class/age; next authorized actor/action; last transition; evidence; continuity.
3. **Timeline:** canonical lifecycle events and decision IDs, ordered by source event time with correction/supersession links.
4. **Evidence/integration:** package evidence manifests, commit/PR, independent verdicts, checkpoints and post-merge closure.
5. **Notebook and communication:** linked decision/hazard/lesson indexes, unresolved decision requests and acknowledgements; neither supplies status.
6. **Risks/blockers:** class, owner, first seen, age, evidence, escalation threshold and safe stop.
7. **Metrics:** formulas/version, window, population, sample size, exclusions and source watermark for the WP-0674 catalog.
8. **Continuity:** current implementation/owner, last verified handoff/reflection, health trigger, fallback and first bounded restart assignment.
9. **Reconciliation:** discrepancies across definitions, PTM, Git/PR, receipts, validation, boards, messages and runtime projections.

## Package drill-down record

Each package drill-down follows the complete field-to-authority map in `Engineering_Campaign_Operational_Status_Model_v1.md` and exposes the canonical reference beside each displayed value. Derived calculations are visibly marked. Source links are resolvable from a fresh checkout; external evidence includes immutable digest and retrieval owner.

## CAMPAIGN-0670 initialization

Populate only by observing sources. WP-0670 through WP-0674 completion receipts are delivery evidence, not acceptance. WP-0675 is not started or implied ready. Gate C remains awaiting an explicit Chief Architect decision. This specification neither changes campaign/package status nor releases a gate.

## Fresh-Chief-Architect recovery checklist

From this page the reviewer can: verify campaign definition/digest; enumerate packages and dependencies; locate latest accepted architecture/gate decision; identify every open branch/PR and validated commit; distinguish execution, validation, merge and acceptance; locate blockers and requested authorities; read material Notebook decisions/messages; inspect continuity readiness; and execute source reconciliation without chat history. Failure of any item is displayed as a blocker.
