# SERIES TASK WP-0026 — Generated Artifact Policy

## Codex Command
Read `collaboration/work_packages/pending/WP-0026_SERIES_generated_artifact_policy.md` and do exactly what it says.

## Mode
SERIES. Implementation/documentation phase. Should follow WP-0025 or run after current operational artifacts are understood.

## Mission
Create a clear Generated Artifact Policy that distinguishes authoritative source files from generated operational projections.

## Why This Is Next
The Estate now produces many generated reports: mailbox summaries, Alfred briefings, validation reports, board integrations, lifecycle reports, dependency graphs, and launch queues. The Estate needs a documented rule for which generated outputs are committed, which are local-only, and how workers should treat them.

## Scope
Add a policy document under an appropriate path such as:

- `docs/operations/Generated_Artifact_Policy_v1.md`

The policy should define:

- authoritative source artifacts
- generated operational projections
- local-only runtime artifacts
- committed generated summaries
- regeneration expectations
- review expectations
- what must never be treated as source of truth

## Required Classifications
At minimum classify:

- `collaboration/messages/*.json` as authoritative message records
- mailbox/status summaries as generated projections
- Operations Board summaries as generated or operational views, depending on existing docs
- work package pending files as authored operational contracts
- completion/review artifacts as institutional evidence
- runtime reports as generated projections unless explicitly promoted
- dashboards as generated operational views

## Expected Outputs
- Generated Artifact Policy v1 document.
- Optional small registry/list of known generated artifact paths if straightforward.
- Tests only if code is added.
- Documentation references from README or operations docs if appropriate.

## Constraints
Do not redesign artifact storage. Do not delete existing generated artifacts. Do not change source-of-truth policy beyond documenting existing Estate principles. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Validation
Confirm policy references existing paths accurately where possible. If adding no code, validation is documentation review plus completion artifact.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0026_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A for documentation/policy clarification. Escalate to Class B only if implementation changes authority or source-of-truth semantics.
