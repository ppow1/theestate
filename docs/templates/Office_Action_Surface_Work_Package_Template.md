# Office Action Surface Work Package Template

## Work package identity

- Work package id:
- Title:
- Target tab/workspace:
- Related Office panel/source:
- Merge class:

## Current noun/status surface

Describe what the tab currently displays, including source artifacts and current UI placement.

## New verbs/actions

| Action | User-facing label | Action class | Authority class | Local read/write behavior | Institutional effect |
| --- | --- | --- | --- | --- | --- |
|  |  | Read / inspect, refresh, export, open source, copy command, create draft, queue request, acknowledge, validate, start/stop service, run safe local command, promote, submit batch, request review, destructive | Safe read-only, safe local generated-artifact update, Steward-confirmed local mutation, authority-gated institutional action, or prohibited |  |  |

## Authority classification

- Authority class for each action:
- Existing authority path used:
- Actions explicitly not permitted:
- Resident Action Authority Boundary impact:
- Validation/merge/governance boundary impact:

## Confirmation behavior

- No-confirmation actions:
- Single-confirmation actions:
- Two-step or destructive confirmations:
- Preview text shown before mutation:
- Recovery/undo/audit story:

## Local command/API surface

- CLI commands exposed or copied:
- API endpoints used:
- Allowlist entry required:
- Local-only guarantee:
- Network/cloud behavior:
- Process/service impact:

## Source artifacts read

| Artifact | Purpose | Required? |
| --- | --- | --- |
|  |  |  |

## Artifacts written

| Artifact | When written | Generated/source-of-truth status | Safety notes |
| --- | --- | --- | --- |
|  |  |  |  |

## UI placement

- Tab/workspace placement:
- Button/menu placement:
- Empty/error/loading states:
- Accessibility notes:
- Copy shown for authority boundary:

## Failure handling

- Command failure display:
- Partial write behavior:
- Validation failure behavior:
- Authority denial behavior:
- Logging/audit behavior:

## Tests

- Unit tests:
- Integration tests:
- CLI/API tests:
- UI rendering tests:
- Regression tests for authority boundaries:

## Validation recipe

The validation recipe must verify:

- target tab/workspace still exists;
- action metadata includes authority classification;
- mutating actions include confirmation behavior;
- local command/API hooks are allowlisted and visible;
- source artifacts read and artifacts written are documented;
- validation behavior is explicit and does not treat UI state alone as success;
- completion receipt is complete.

## Completion receipt

The completion receipt must include:

- work_package_id;
- codex_status;
- completed_at;
- branch;
- pull_request_url or not-applicable reason;
- summary;
- target tab/workspace;
- actions added;
- authority classes;
- files changed;
- tests run;
- validation commands run;
- known limitations;
- ready_for_ca_review;
- merge_authority.
