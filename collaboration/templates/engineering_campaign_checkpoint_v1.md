# <CAMPAIGN-ID> — <checkpoint> Evidence

- **Campaign / checkpoint:** `<CAMPAIGN-ID / name>`
- **Prepared by / at:** `<identity / ISO-8601 UTC>`
- **Integration base:** `<branch and immutable SHA>`
- **Outcome:** `<pass | fail | blocked | not_applicable>`
- **Authority requested:** `<review lane; this record grants no acceptance>`

| Package | Pending source | PR | Head / merged commit | Validation report | Receipt | Acceptance state |
|---|---|---|---|---|---|---|
| `<WP-ID>` | `<path>` | `<ref>` | `<sha / sha>` | `<path>` | `<path(s)>` | `<explicit state>` |

## Dependency, merge-order, and contract-freeze reconciliation
`<authoritative dependency refs, actual order, shared-file decisions, conflicts and owners>`

## Checkpoint validation
| Exact command/recipe | Outcome | Evidence |
|---|---|---|
| `<command>` | `<pass/fail/blocked/N/A>` | `<path/reference>` |

## Missing, stale, contradictory, or waived evidence
`<explicit entries, authority reference, expiry and owner; never infer pass>`

## Recovery and next authorized action
`<rollback/rework and bounded request; checkpoint is not a campaign gate decision>`

