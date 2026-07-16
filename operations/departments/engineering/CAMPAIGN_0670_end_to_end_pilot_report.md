# CAMPAIGN-0670 End-to-End Pilot Report

Date: 2026-07-16
Pilot: `PILOT-0670-01` / package `WP-0675`
Disposition: **completed as a bounded repository dry-run; acceptance not granted**

## Boundary and method

The pilot used CAMPAIGN-0670 itself as the approved, non-production-destructive fixture. WP-0670 through WP-0674 are the decomposition and integrated inputs; WP-0675 is the one implementation branch and review handoff. Repository definitions, receipts, Git, tests, and the readiness record are live. PTM event writes, workforce reservation, Dispatch submission, a second provider run, merge, post-merge controller execution, and protected decisions were simulated because this documentation pilot was not authorized to mutate those systems or merge/accept itself. Each simulated boundary used the contract's fail-closed result rather than fabricating success.

## Lifecycle trace

| Stage | Mechanism/evidence | Result and boundary |
|---|---|---|
| approved campaign intake | campaign authority basis and objective; WP-0671 intake contract | Fixture assumes the existing campaign definition is the durable approved input; absence of a separate parent decision remains a condition. |
| decomposition | six Pending definitions and dependency order | Live repository evidence; one primary campaign and WP unit preserved. |
| readiness evaluation | WP-0671 readiness model; receipts; runtime readiness record | Dry-run evaluates `conditionally_ready`; missing explicit Gate A-C/architecture decisions fail closed. |
| staffing/capability | WP-0675 owner/lane plus Engineering charter | Codex assignment is observed; canonical staffing/capacity record is mocked and therefore cannot authorize production execution. |
| lane selection | WP-0672 contract; declared Codex lane | Codex is suitable; selection is evidence, not authority. Provider reservation/health is mocked. |
| Dispatch/Codex handoff | user handoff and package definition | Direct Codex handoff is the fixture boundary. No Dispatch event is asserted; a production package would stop until eligible Dispatch exists. |
| branch and PR | branch `codex/wp-0675-operational-readiness-acceptance`; WP-scoped commit/PR workflow | Live branch/commit; PR is created only after validation and is review evidence, not merge/acceptance. |
| evidence collection | five reports, runtime JSON, receipt, Git diff | Live, repository-addressable evidence. |
| package validation | exact commands in receipt | Live self-validation; independent validator acknowledgement remains absent. |
| integration checkpoint | reconciliation matrix and prerequisite merge history | Earlier outputs are integrated in the base; checkpoint decision itself is mocked/absent and fails closed. |
| campaign validation | assessment matrix and failure exercises | Live document/content/JSON/test checks; no protected decision inferred. |
| operational readiness | readiness assessment and runtime projection | **Conditionally Ready**; protected gates and post-merge evidence remain open. |
| Chief Architect acceptance preparation | acceptance package | Prepared only; Chief Architect decision absent. |
| Steward-facing final package | acceptance package plus exact conditions | Prepared only; no Steward decision, archive, or acceptance record created. |

## Result

The trace proves that one coherent contract can carry stable campaign/package identities, bounded provider execution, Git evidence, validation, recovery, and acceptance preparation without routine Steward scheduling. It does **not** prove live PTM/Dispatch/provider availability or post-merge readiness. Those mocked boundaries are rollout prerequisites, not hidden passes.

## Evidence and rollback

Evidence is the WP-0670–WP-0675 receipt set, this report, the authority/failure reports, assessment, acceptance package, runtime record, Git commit, and PR. Rollback is revert of the WP-0675 commit; no production runtime, merge state, protected decision, or acceptance authority was changed.
