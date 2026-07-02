# SERIES TASK WP-0021 — Personnel Identity and Mailbox Resolver

## Codex Command
Read `collaboration/work_packages/pending/WP-0021_SERIES_personnel_identity_mailbox_resolver.md` and do exactly what it says.

## Mode
SERIES. Implementation-phase. Should follow WP-0014, WP-0015, WP-0019, and WP-0020.

## Mission
Implement a conservative registry-backed resolver that maps Estate personnel, offices, workers, employee IDs, and mailbox IDs to canonical mailbox destinations.

## Why This Is Next
The Estate now uses Communication Bus messages, worker mailboxes, Alfred operational briefing, and Helen HR onboarding. Addressing is still partly implicit. A resolver is needed so future tools do not guess whether a destination is an office, employee, mailbox, or worker.

## Scope
Use existing registry sources where present:

- `data/registry/personnel.json`
- `data/registry/mailboxes.json`
- `data/registry/residents.json`

Implement a small module such as:

- `src/estate/core/personnel_identity.py`

The resolver should support lookups for:

- `employee.<id>`
- `mailbox.<id>`
- `office.chief_architect_2`
- `office.chief_architect_3`
- `office.chief_architect_4`
- known worker names such as `worker.audit`, `worker.implementation`, `alfred`, and `helen`

## Expected Outputs
- Resolver module.
- CLI or helper if consistent with existing patterns, for example `personnel-resolve --actor <actor>`.
- Tests covering employee, mailbox, office, and worker destination resolution.
- Documentation note describing resolver boundaries.

## Constraints
Do not create final HR authority. Do not create final clearance/security policy. Do not redesign the Communication Bus. Do not invent missing registry facts. Missing or ambiguous mappings should produce warnings, not fabricated identities. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Validation
Run relevant tests. Demonstrate resolution for Chief Architect #3, Chief Architect #4, Alfred, Helen, and at least one worker destination if registry data supports it.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0021_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded registry-backed implementation. Escalate to Class B only if the implementation creates new authority, security, or HR policy.
