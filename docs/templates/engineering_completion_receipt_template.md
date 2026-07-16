# <WP-ID> Completion Receipt

- **Campaign:** `<CAMPAIGN-ID>`
- **Work package:** `<WP-ID — title>`
- **Execution state:** `<partial | implementation_complete | blocked | abandoned>`
- **Lifecycle state requested:** `<package_validation | integration_review | acceptance_preparation>`
- **Acceptance status:** `not accepted` unless linked to a separate decision
- **Worker / lane / provider:** `<identity / lane / provider or N/A rationale>`
- **Branch / base / head:** `<branch / SHA / SHA>`
- **PR / merged commit:** `<reference or not_yet_recorded>`
- **Produced at:** `<ISO-8601 UTC>`

## Implementation and files
`<summary and repository-relative changed-file inventory>`

## Commands and validation
| Command / recipe | Environment | Outcome | Evidence |
|---|---|---|---|
| `<exact command>` | `<details>` | `<pass/fail/blocked/N/A>` | `<path/reference>` |

## Artifacts, contracts, and dependencies
`<reports/artifacts; dependency and interface impact; campaign freeze/shared-file disposition>`

## Warnings and recovery
`<unresolved limitations, expiry/staleness, rollback/recovery instructions>`

## Acknowledgements
- Executor: `<identity, acknowledgement, time>`
- Validator: `<identity/reference or not_yet_recorded>`
- Integration owner: `<identity/reference or not_yet_recorded>`
- Requested acceptance lane: `<authority>`

This receipt is evidence of submission only; it does not substitute for validation, merge, readiness, or acceptance.

