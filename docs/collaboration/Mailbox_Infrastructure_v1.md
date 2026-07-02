# Mailbox Infrastructure v1

Status: Implemented  
Classification: Estate Internal

## Purpose

Mailbox Infrastructure v1 gives Estate personnel, functional queues, and external ChatGPT-based workers a stable way to discover repository-backed messages without relying on directory enumeration. The generated mailbox index is available at `collaboration/mailboxes/index.json` as a known fetchable file.

## Personnel Mailbox Model

Personnel identity is owned by the personnel registry at `data/registry/personnel.json`. Employee IDs are plain numeric identifiers and do not encode office, title, worker class, or role.

Seeded personnel identities are:

- `0` — Reserved / Special Institutional Identity. This identity is reserved and has no operational behavior assigned by this capability.
- `1` — Steward / Founder.
- `2` — Chief Architect #1.
- `3` — Chief Architect #2.
- `4` — Chief Architect #3.

For seeded personnel, `employee_id` and `mailbox_id` are the same numeric value.

## Functional Mailbox Model

Functional mailbox identity is owned by the functional mailbox registry at `data/registry/mailboxes.json`. Functional mailboxes support offices, services, queues, work packages, temporary operational functions, and task-specific intake.

Allowed `mailbox_type` values in v1 are:

- `personnel`
- `office`
- `service`
- `queue`
- `work_package`
- `temporary`

Functional mailboxes may receive messages or work, but they do not replace personnel accountability. When accountability is required, a specific employee, worker, or service must still claim, execute, sign, or acknowledge the work.

## Mailbox ID Ranges

Mailbox IDs `0` through `9999` are reserved for personnel identities.

Mailbox IDs `10000` and above are reserved for functional mailboxes.

Mailbox directory names are zero-padded to four digits for IDs below `10000`, and plain numeric strings for IDs `10000` and above. Examples: `0003`, `0004`, `10001`.

## Relationship Between Employee ID and Mailbox ID

Personnel entries include both `employee_id` and `mailbox_id`. For seeded personnel, these values match. The registry remains the source for the relationship; code should not infer titles or offices from numeric IDs.

## Message Source of Truth Rule

Messages remain the source of truth. In v1, canonical message envelopes are read from:

```text
collaboration/messages/*.json
```

Mailbox folders and `collaboration/mailboxes/index.json` are discovery aids. They do not replace or supersede message envelopes.

## Index Generated-Artifact Rule

The mailbox index is a generated operational artifact. It is rebuilt by scanning the registries and current message files. Workers should use it to discover relevant messages, but they must not treat it as the authoritative message store.

The index includes message path, source, destination, resolved numeric destination fields, title, message type, priority, status, acknowledgment metadata, creation timestamp, and warnings for unresolved or malformed messages.

## Legacy Destination Compatibility

Mailbox Infrastructure v1 supports legacy destination strings already used by existing messages:

- `office.chief_architect_2` resolves to `employee_id: 3` and `mailbox_id: 3`.
- `office.chief_architect_3` resolves to `employee_id: 4` and `mailbox_id: 4`.

If a message includes `destination_employee_id`, that explicit numeric field takes precedence over legacy destination text. If a message includes `destination_mailbox_id`, it is used when no explicit destination employee ID is present.

Unresolved destinations and malformed messages are included in the generated index with warning metadata rather than causing generation to fail.

## How to Run `mailbox-index`

From the repository root:

```bash
PYTHONPATH=src python -m estate.cli.main mailbox-index --json
```

The command reads `data/registry/personnel.json`, reads `data/registry/mailboxes.json`, scans `collaboration/messages/*.json`, ensures mailbox directories exist, writes `collaboration/mailboxes/index.json`, and prints a JSON summary.

The command does not require network access, browser authentication, or `A:\theestate`.

## Limitations

- v1 indexes messages in `collaboration/messages/*.json`; it does not move or destroy existing messages.
- v1 does not define complex mailbox permissions.
- v1 does not define security clearance semantics. Registry `security_clearance` values are metadata only unless another Estate standard defines them.
- Functional mailboxes do not assign accountability by themselves.
- The index is only as current as its most recent generation.

## Future Work

- Add richer mailbox status reporting if operational practice requires it.
- Add claim/acknowledgment workflows that preserve personnel accountability.
- Add transport adapters that consume the generated index without replacing message envelopes as the source of truth.
- Add retention and archive policies only through a future governance-approved work package.
