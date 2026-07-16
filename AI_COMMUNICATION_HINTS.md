# AI_COMMUNICATION_HINTS.md

Status: Canonical fast-recovery pointer for Estate communication artifacts.  
Classification: Estate Internal

Use this file when a worker has forgotten how to park an idea, send a repository-backed message, discover mailbox contents, or decide which communication mechanism is appropriate.

This is a quick-reference plate. It does not replace the governing board, mailbox, collaboration, or work-package documents.

## Fast Decision

| Need | Use | Authoritative location |
|---|---|---|
| Preserve a valuable idea without interrupting current work | Parking Lot | `operations/boards/parking_lot.md` and, for nontrivial entries, `collaboration/parking_lot/PL-####-slug.md` |
| Tell another office or worker something durably | Repository-backed message | `collaboration/messages/*.json` |
| Discover messages for an office or employee | Mailbox index | `collaboration/mailboxes/index.json` |
| Assign executable governed work | Work package | Existing work-package pipeline and office numbering rules |

## Parking an Idea

1. Read the current Parking Lot and `collaboration/parking_lot/` before selecting the next unused `PL-####` ID.
2. Add a board row containing ID, idea, category, priority, originator, date captured, status, optional target milestone, and promotion condition.
3. For a nontrivial idea, create `collaboration/parking_lot/PL-####-slug.md` with: Idea, Why It Is Parked, Promotion Condition, Explicit Non-Action, and Related Evidence.
4. Do not begin implementation merely because the idea was captured. Promotion requires an intentional decision.

## Sending a Repository-Backed Message

1. Resolve the sender and destination from `data/registry/personnel.json`, `data/registry/mailboxes.json`, and `collaboration/mailboxes/index.json`. Do not guess IDs from titles.
2. Create a unique JSON file in `collaboration/messages/`.
3. Include at least: `message_id`, `created_at`, `source`, source ID, `destination`, destination ID or mailbox ID, `message_type`, `title`, `priority`, `status`, `requires_ack`, `classification`, and `summary`.
4. The message file is authoritative. Mailbox folders and indexes are discovery aids.
5. When operating in a local checkout, rebuild discovery indexes from the repository root with:

```text
PYTHONPATH=src python -m estate.cli.main mailbox-index --json
```

## Recovery Commands

To park an idea:

> Read `AI_COMMUNICATION_HINTS.md`. Park this idea without beginning implementation: [idea].

To send a message:

> Read `AI_COMMUNICATION_HINTS.md`. Send a repository-backed message from [sender] to [destination]: [message].

When uncertain, stop and read the governing source instead of inventing a new communication path.

## Engineering Campaign Communication

For Engineering campaign/package handoffs, blockers, acceptance requests, and escalation patterns, read `docs/operations/Engineering_Communication_and_Escalation_Standard_v1.md`. It applies the rules above and does not make messages or mailboxes a status registry.
