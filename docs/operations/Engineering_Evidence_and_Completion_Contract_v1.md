# Engineering Evidence and Completion Contract v1

## Purpose and authority

This contract is the Engineering Department's evidence profile over the existing work-package, PTM, Dispatch, provider, Git/PR, validation, operational-readiness, and acceptance records. It creates no queue, validator, readiness controller, or acceptance authority. A work package is the execution unit; its primary campaign is the coordination unit. Missing, contradictory, expired, or unverifiable evidence fails closed.

## Minimum evidence bundle

Every package completion submission MUST contain the following durable, repository-relative references. Chat, a worker assertion, a branch name without a commit, or a receipt alone is not evidence.

| Field | Requirement and authoritative source |
|---|---|
| identity | Literal work-package ID/title and primary campaign ID from the pending package/campaign record. |
| attribution | Worker, execution lane, selected provider and provider execution/attempt reference; use `not_applicable` with a reason when no provider ran. |
| source | Owned branch, immutable base and head commit SHA, PR URL/number when opened, and merged commit when merged. |
| changes | Repository-relative changed-file inventory and implementation summary, reproducible from the commit range. |
| validation | Exact commands, environment/preconditions, outcomes, timestamps, report/artifact paths, and validator identity. Failed or skipped required checks remain visible. |
| limitations | Warnings, flaky/contradictory results, missing recipes, environmental limits, unresolved risks, and expiry/staleness. |
| contracts | Dependencies and affected interfaces, schemas, authority boundaries, shared files, and campaign contract-freeze impact. |
| recovery | Revert/rollback command or recovery steps, retained state/artifact locations, and data-migration considerations. |
| handoff | Requested acceptance lane, current lifecycle state, and human- and machine-readable completion-receipt paths. |

Repository evidence is attributable when it names the producing actor/provider and immutable source reference. Generated artifacts MUST be committed unless secrets, personal data, size, or volatility policy forbids it; then the receipt records the governed external locator, digest, retention owner, and access limitation. Secrets MUST NOT be committed.

## Evidence truth and traceability

The trace key is `(campaign_id, work_package_id)`. A reviewer follows it from campaign and pending package, through readiness/dependency records, Dispatch/provider attempt (when applicable), branch commits and PR, validation reports, merge commit, campaign checkpoint, readiness report, and acceptance record. Each record links backward; later records never rewrite earlier results.

Evidence states are `present`, `missing`, `stale`, `contradictory`, or `not_applicable`. Only a named authority may approve a waiver, and its reference, scope, expiry, and rationale remain attached. `not_applicable` is a reasoned finding, never a silent omission.

## Completion receipts

Create both:

* `collaboration/work_packages/completions/<WP-ID>_completion_receipt.md`, based on `docs/templates/engineering_completion_receipt_template.md`; and
* `collaboration/work_packages/completions/<WP-ID>_completion_receipt.json`, based on `docs/templates/engineering_completion_receipt_v1.json` when machine processing is required by the package or campaign.

The Markdown and JSON records MUST agree on identity, state, commits, validation outcome, limitations, and requested acceptance lane. Duplicate receipts are an error unless one explicitly supersedes the other by path and commit while retaining both histories. The executor acknowledges production; the validator acknowledges observed results; the integration owner acknowledges merge evidence; the Chief Architect records engineering acceptance separately; the Steward records final institutional acceptance separately. An acknowledgement is not a signature by a later authority.

Allowed receipt execution states are `partial`, `implementation_complete`, `blocked`, and `abandoned`. A receipt MUST NOT say `complete`, `validated`, `integrated`, `accepted`, or `closed` unless the corresponding authoritative report/commit/decision reference exists. A failed validation cannot be recorded as completion. Receipt creation requests review; it cannot substitute for validation, merge, readiness, or acceptance evidence.

## Freshness, correction, and retention

Validation binds to the tested head SHA and declared environment. A new commit, changed dependency/contract, superseding package, or relevant environment drift makes affected evidence stale and requires rerun or an explicit reviewer finding. Corrections append or supersede; they do not delete failed attempts. Branch deletion is permitted only after immutable commits, PR history, reports, and receipts remain addressable under repository retention policy.

