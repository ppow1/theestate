# Campaign-Level Codex Execution Capability

Status: Implemented by WP-0678  
Owner: Chief Architect  
Execution provider: Codex

## Boundary

`CodexCampaignExecution` is a durable campaign controller, not a scheduler, merge authority, or acceptance authority. An approved manifest is handed to the controller once. Execution stays on its declared non-protected campaign branch, each work package remains atomic, and the eventual campaign pull request remains a human-created review and acceptance surface.

The controller never invokes Codex, creates or merges a pull request, accepts a package, or accepts a campaign. Provider adapters consume eligible package identifiers and report their commit or failure. Reviewers explicitly release internal gates.

## Manifest contract

A `CodexCampaignManifest` records the campaign source and ID, campaign branch, approving authority, ordered packages, dependencies, explicitly approved parallel groups, and internal review gates. Registration rejects duplicate package IDs, unknown dependencies or gate feeders, protected branches, missing approval, and undeclared parallel execution.

Each `CodexCampaignPackage` records its authoritative source, dependencies, parallel group, state, attempt count, failure, and its single bounded commit. A second commit cannot be recorded for the package.

## Execution protocol

1. Register the approved manifest once.
2. Start only while the caller is on the manifest's campaign branch.
3. Ask `next_launches()` for the dependency-eligible package or approved parallel wave.
4. Mark each selected package running and hand it to the Codex provider adapter.
5. On success, record exactly one commit for that package. On failure, record the failure and stop the campaign for reconciliation.
6. When all feeders for an internal gate complete, the controller enters `awaiting_review`; no next launch is returned until an identified reviewer approves that gate.
7. After interruption, construct a new controller and load the JSON state from `runtime/codex_campaigns/<campaign-id>.json` before continuing.
8. Reconcile a failed package explicitly as `retry` or `skip`. Retry returns it to dependency planning; skip leaves the campaign paused for a governing decision.
9. After every package succeeds, the controller enters `awaiting_acceptance`. The branch and bounded commits may then be presented as one campaign pull request. This state is not merge or institutional acceptance.

Every transition appends a timestamped event to the same durable state envelope. This gives recovery and presentation an ordered record without creating another authoritative campaign definition.

## Failure and recovery rules

- A package failure sets `reconciliation_required` and suppresses all launches, including otherwise eligible parallel siblings.
- A retry preserves attempt history and increments the count at its next start.
- A skip never implies success; it pauses execution and therefore cannot satisfy downstream dependencies.
- Completed package commits are retained through failure and restart. Operators reconcile from persisted state rather than terminal or chat memory.
- Branch mismatch, premature launch, continuation through a review gate, and duplicate commit recording fail closed.

## Campaign pull-request presentation

The campaign pull request should list the manifest source, campaign branch, package-to-commit map, gate approvals, validation evidence, reconciliations, and unresolved warnings. Creation, review, merge, and protected acceptance remain outside this controller and require the applicable human authority.
