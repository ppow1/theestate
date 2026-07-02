# SERIES TASK WP-0015 — Message Acknowledgement and Reply Flow

## Steward Command
Open `collaboration/work_packages/pending/WP-0015_SERIES_message_acknowledgement_reply_flow.md` in `ppow1/theestate` and execute the directions inside.

## Mode
SERIES. Depends on WP-0014 mailbox destination coverage.

## Mission
Add a minimal acknowledgement and reply/threading flow for Communication Bus messages.

## Why This Is Next
Chief Architect collaboration now needs durable acknowledgement, reply chains, and review traceability. Current message files can be sent, but the Estate needs a simple way to mark that messages requiring acknowledgement were received and answered.

## Scope
- Extend message handling using existing message JSON files.
- Support fields such as `thread_id`, `reply_to`, `acknowledges`, `requires_ack`, `ack_status`, and `status` where appropriate.
- Add a simple CLI or helper to generate acknowledgements and replies if consistent with existing CLI patterns.
- Update mailbox/index summaries to surface acknowledgement-required messages.
- Do not redesign the Communication Bus.

## Expected Outputs
- Minimal reply/acknowledgement support.
- Tests covering acknowledgement-required messages, replies, and thread grouping.
- Documentation update for message acknowledgement and reply behavior.

## Constraints
Do not create new governance. Do not change authority semantics. Do not require network access. Do not edit ledger/devlog.

## Validation
Run relevant tests. Demonstrate a message with `requires_ack=true` can be acknowledged and a reply can reference the original message.

## Codex Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0015_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A with CA verification. If implementation changes Communication Bus semantics beyond acknowledgement/threading, escalate to Class B.
