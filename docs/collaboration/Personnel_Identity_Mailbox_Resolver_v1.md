# Personnel Identity and Mailbox Resolver v1

The personnel identity resolver maps Estate addressing strings to canonical destinations using existing registry evidence only.

## Registry sources

- `data/registry/personnel.json` for employee IDs, personnel display names, offices, resident links, and personnel mailbox IDs.
- `data/registry/mailboxes.json` for functional office, queue, service, work-package, and temporary mailboxes.
- `data/registry/residents.json` for resident names and resident IDs.

## Supported lookup forms

- `employee.<id>` and unique employee aliases derived from registry display names or current titles.
- `mailbox.<id>` and unique functional mailbox aliases derived from registry display names or owning offices.
- `office.<slug>` for unique personnel title/display-name office aliases such as `office.chief_architect_3` and `office.chief_architect_4`, or unique functional office mailbox aliases.
- Known routing workers from the Alfred routing engine, including `worker.audit`, `worker.implementation`, and `alfred.review`.
- Resident names when a conservative registry mapping exists. Helen resolves through her personnel registry entry. Alfred resolves to the registered Alfred Routing Intake mailbox.

## Boundaries

The resolver is intentionally conservative. It does not create final HR authority, clearance policy, or Communication Bus routing policy. Missing or ambiguous registry mappings return warnings and unresolved results instead of fabricated identities. Worker destinations resolve to worker routes, not personnel mailboxes, unless a registry-backed mailbox exists separately.

Use the CLI helper with:

```bash
python -m estate.cli.main personnel-resolve --actor office.chief_architect_4 --json
```
