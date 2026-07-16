# Engineering Validation and Integration Lifecycle v1

## Governed lifecycle

```text
implementation complete
  -> self-validation
  -> package validation
  -> integration validation
  -> campaign checkpoint validation
  -> operational-readiness validation
  -> acceptance preparation
```

The existing package recipe and `operations/validation/` reports remain authoritative. Stages do not collapse: passing one cannot imply a later stage. Outcomes are `pass`, `fail`, `blocked`, or `not_applicable` (N/A requires rationale and named reviewer). The author may self-validate but MUST NOT approve package validation, integration, protected readiness, or acceptance.

| Stage | Responsible party | Required input and command source | Durable evidence | Rework / escalation |
|---|---|---|---|---|
| Implementation complete | Executing worker/provider | Pending package, ready dispatch/handoff, head SHA, changed-file inventory | Completion receipt plus commits/provider result | Partial work returns to implementation; scope/authority drift escalates to Chief Architect. |
| Self-validation | Executing worker/provider | Exact pending-package recipe, changed-component tests, repository checks | Receipt command log and generated reports | Fix and rerun with every attempt retained; missing recipe is `blocked`, not pass. |
| Package validation | Validator other than the approving author; Validation/Chief Architect delegate | Pending recipe and `operations/validation/scripts/validate_work_package.ps1 -WorkPackageId <ID>` where supported | `operations/validation/reports/<WP-ID>_validation.md` or recipe-specified report | Fail returns bounded findings to worker. After two unchanged failed rework cycles, contradictory results, or authority ambiguity, escalate to Chief Architect. |
| Integration validation | Integration owner/reviewer, not sole author-approver | PR diff, base/head SHAs, package reports, shared-file/contract-freeze checks, merge-order plan | PR checks/review and integration report/checkpoint | Conflict owner resolves; stale base is rebased/merged then all invalidated checks rerun. Unresolved shared-contract conflict blocks merge. |
| Campaign checkpoint | Campaign integration owner with package validators | Merged commit references, dependency/order record, package reports, checkpoint template | `collaboration/campaigns/checkpoints/<CAMPAIGN-ID>_<checkpoint>_evidence.md` | Any missing/failed feeder blocks checkpoint; campaign authority resolves cross-package contradiction. |
| Operational readiness | Existing operational-readiness controller/authorized reviewers | Existing readiness recipe/controller and merged deployment candidate | Existing readiness recipe/report under `operations/validation/` | Preserve fail/blocked result and follow controller recovery/escalation; Engineering cannot waive it. |
| Acceptance preparation | Engineering/Chief Architect review coordinator | Complete chain plus readiness outcome and unresolved-risk register | Review packet linking evidence; separate acceptance decision | Rejection returns package to the explicit stage named by the decision; no self-approval. |

Retries are bounded by the package recipe, provider policy, or two materially identical failures by default. A retry is a new recorded attempt, not replacement of the old result. Environmental unavailability is `blocked`; an optional check may be N/A only where the recipe permits it. Security, privacy, protected-state, architecture-authority, persistent flake, or evidence-integrity issues escalate immediately to the relevant authority and Chief Architect.

## Integration contract

One implementation branch and one PR per work package is the default. A grouped integration PR is allowed only when the campaign or Chief Architect explicitly authorizes it, names included package IDs/commits, explains why individual PRs are insufficient, retains package-level validation/receipts, and names an integration owner. It never converts multiple packages into one evidence identity.

Before work begins, packages declare owned paths and shared-file collision controls. Contract-freeze files change only in the owning package or by explicit integration-owner decision. Merge order follows hard dependencies, then the campaign launch/integration plan; an earlier merge does not imply downstream eligibility. Midpoint integration branches/checkpoints are temporary review surfaces, not new authoritative status stores, and must record base, included commits, validation, owner, and disposition.

The package owner resolves its code conflict; the contract owner resolves semantic/shared-contract conflicts; the integration owner decides sequencing; the Chief Architect decides architecture ambiguity. Stale-base work must update from the current integration base and rerun affected validation. A superseded package stops, records the superseding authority/reference and preserved head, and cannot submit a competing completion claim. Abandoned branches retain a receipt and recoverable commit/reference.

After merge, record the actual merged commit (not merely the PR head), rerun merge-sensitive and campaign integration checks, update the checkpoint link, and keep pre-merge results. Campaign state links package ID, PR, head, merged commit, validation report, receipt, and current acceptance state; it does not infer any of them.

## Failure and recovery matrix

| Condition | Required explicit state and recovery |
|---|---|
| Partial implementation | `partial`; preserve commits/artifacts, remaining scope, safe restore point, then resume or re-scope by authority. |
| Validation failure | `fail`; retain output, return to implementation, create a new attempt after repair. |
| Missing recipe | `blocked`; validation owner supplies/approves a recipe—worker may not invent a passing substitute. |
| Flaky/contradictory tests | `blocked`; retain all runs, isolate environment/seed, escalate after bounded retries. |
| Integration conflict | `blocked_integration`; owners resolve against current base and rerun affected checks. |
| Provider failure | Record failed attempt/reconciliation; retry/fallback only through existing routing authority, with new provider attribution. |
| Branch abandonment | `abandoned`; preserve head/recovery notes and release ownership explicitly. |
| Duplicate receipt | `evidence_conflict`; designate a superseding receipt without deleting either and revalidate truth. |
| Stale evidence | `stale`; identify invalidating change and rerun affected stages on the current SHA/environment. |
| Post-merge regression | Open a governed repair/revert path, link original merge/validation, and return integration/readiness to `fail` or `blocked`. |
| Acceptance rejection | Record the decision and reasons separately; return to the named prior stage. Prior evidence remains historical. |

