# SERIES TASK WP-0023 — Mailbox Synchronization Duty Runtime

## Codex Command
Read `collaboration/work_packages/pending/WP-0023_SERIES_mailbox_synchronization_duty_runtime.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0021 and WP-0022.

## Mission
Implement the first operational runtime support for Mailbox Synchronization Duty without finalizing HR/security policy or fixed polling cadence.

## Why This Is Next
The Estate now depends on mailboxes for institutional collaboration. Personnel need an operational way to know when mailbox synchronization is required at task boundaries, before architectural work, before closing work, and during Check for Updates.

## Scope
Add a lightweight mailbox synchronization duty checker that can report whether an actor has mailbox obligations.

Inputs should include, where present:

- `collaboration/messages/*.json`
- mailbox index/status outputs
- personnel/mailbox resolver from WP-0021
- Check for Updates outputs from WP-0022

The checker should identify:

- unread/open messages
- acknowledgement-required messages
- replies waiting for actor attention
- messages assigned to actor, office, employee, mailbox, or worker aliases
- synchronization warnings for unresolved identity

## Expected Outputs
- Runtime report such as `runtime/mailboxes/synchronization_duty.json`.
- Human-readable output such as `operations/mailboxes/synchronization_duty.md`.
- CLI or helper if consistent with existing patterns, for example:

```bash
PYTHONPATH=src python -m estate.cli.main mailbox-sync-duty --actor office.chief_architect_3 --json
```

## Constraints
Do not impose a fixed polling interval. Do not create final HR policy. Do not create final security clearance policy. Do not redesign mailboxes or Communication Bus. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Add tests for:

- actor with no obligations
- actor with open messages
- actor with acknowledgement-required messages
- unresolved identity warning
- output generation

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0023_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded operational support. Escalate to Class B only if implementation creates final HR, security, or polling policy.
