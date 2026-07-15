# AI_COMMUNICATION_HINTS.md

Status: Canonical fast-recovery pointer for Estate communication artifacts.  
Classification: Estate Internal

Use this file when a worker has forgotten how to park an idea, send a repository-backed message, discover mailbox contents, or decide which communication mechanism is appropriate.

This file is a quick-reference plate. It does not replace the governing collaboration, mailbox, board, or work-package documents.

## Fast Decision

| Need | Use | Authoritative location |
|---|---|---|
| Preserve a valuable idea without interrupting current work | Parking Lot | `operations/boards/parking_lot.md` and, for substantial entries, `collaboration/parking_lot/` |
| Tell another Estate office or worker something durable | Repository-backed message | `collaboration/messages/*.json` |
| Discover messages addressed to an office, employee, or mailbox | Mailbox index | `collaboration/mailboxes/index.json` and generated mailbox views |
| Assign executable work with scope, ownership, evidence, and completion criteria | Work Package | Estate work-package pipeline and governing work-package standards |

## Parking an Idea

Use the Parking Lot when the idea is valuable but should not interrupt active execution.

1. Read the current `operations/boards/parking_lot.md` completely.
2. Check `collaboration/parking_lot/` for newer detailed entries before choosing the next unused `PL-####` identifier.
3. Add the board entry with all required fields:
   - ID;
   - idea;
   - category;
   - priority;
   - originator;
   - date captured;
   - status;
   - optional target milestone;
   - promotion condition.
4. For a substantial idea, create `collaboration/parking_lot/PL-####-descriptive-slug.md` containing:
   - Idea;
   - Why It Is Parked;
   - Promotion Condition;
   - Explicit Non-Action;
   - Related Evidence.
5. Link the board entry to the detailed record.
6. Do not silently promote the idea into active work. Promotion requires an intentional decision or authorization.

Standard instruction:

> Read `AI_COMMUNICATION_HINTS.md`. Park this idea without beginning implementation: [idea].

## Sending a Repository-Backed Message

Use a repository-backed message when one office, worker, or employee must communicate durable information to another.

1. Resolve identities from the Estate registries. Do not guess employee IDs, mailbox IDs, or office aliases from titles.
2. Create a uniquely named JSON record in `collaboration/messages/`.
3. Include the core message fields:
   - `message_id`;
   - `created_at`;
   - `source`;
   - `source_employee_id` when applicable;
   - `destination`;
   - `destination_employee_id` when applicable;
   - `destination_mailbox_id` when applicable;
   - `message_type`;
   - `title`;
   - `priority`;
   - `status`;
   - `requires_ack`;
   - `classification`;
   - `summary`.
4. Add structured fields such as findings, recommendation, requested action, evidence, or due conditions when they improve clarity.
5. Treat `collaboration/messages/*.json` as the source of truth. Mailbox folders and indexes are discovery aids, not the authoritative message record.
6. When operating in a local checkout, rebuild mailbox discovery data from the repository root with:

```text
PYTHONPATH=src python -m estate.cli.main mailbox-index --json
```

Standard instruction:

> Read `AI_COMMUNICATION_HINTS.md`. Send a repository-backed message from [source] to [destination] stating: [message].

## Discovering Mail

Use mailbox views to find messages, not to create the authoritative message record.

- Mailbox discovery index: `collaboration/mailboxes/index.json`
- Personnel registry: `data/registry/personnel.json`
- Functional mailbox registry: `data/registry/mailboxes.json`
- Authoritative messages: `collaboration/messages/*.json`

Destination aliases may include office, employee, mailbox, direct ID, or worker-name forms. Explicit destination IDs override ambiguous text labels.

## Work Package Boundary

A message is not a work package.

Use a work package when the request requires bounded execution, an owner, dependencies, validation, evidence, and a completion condition. A message may request or discuss work, but it does not replace governed assignment and acceptance.

## Recovery Rule

When uncertain:

1. Preserve without acting: Parking Lot.
2. Communicate durably: Repository-backed message.
3. Discover communications: Mailbox index.
4. Assign executable work: Work Package.

Do not invent a new communication mechanism when an existing Estate mechanism fits.