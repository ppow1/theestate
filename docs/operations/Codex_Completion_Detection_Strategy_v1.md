# Codex Completion Detection Strategy v1

## Purpose

This strategy defines how the Estate detects local Codex work-package completion before any GitHub merge occurs. It deliberately treats merged GitHub state as a downstream publication event, not the primary completion signal.

## Current Completion Flow

1. A Steward or Chief Architect selects a work package from `collaboration/work_packages/pending/`.
2. The Codex handoff generator emits a copy-ready command that tells Codex to read the package and do exactly what it says.
3. Codex edits local repository files on the current branch.
4. Codex creates a local completion record under `collaboration/work_packages/completions/`.
5. The Steward or Chief Architect reviews the branch, changed artifacts, test results, and completion record.
6. Only after approval may the branch be merged.

The completion record is therefore the first durable local signal that Codex believes the package is complete.

## Primary Local Completion Signal

The primary completion signal is a work-package completion record using the standard filename:

```text
collaboration/work_packages/completions/<WORK_PACKAGE_ID>_codex_done.json
```

A completion record is considered locally complete when all of the following are true:

- The JSON file exists and parses successfully.
- It includes the standard fields: `work_package_id`, `codex_status`, `completed_at`, `branch`, `pull_request_url`, `summary`, `files_changed`, `tests_run`, `known_limitations`, `ready_for_ca_review`, and `merge_authority`.
- `codex_status` is `done` or `completed`.
- `ready_for_ca_review` is `true`.
- The `work_package_id` matches the expected package.

This signal means “ready for Chief Architect or Steward review,” not “merged,” “approved,” or “published.”

## Observable Signals Before Merge

The Estate can inspect several local signals before GitHub merge state exists:

| Signal | Source | Meaning | Limitation |
| --- | --- | --- | --- |
| Completion record | `collaboration/work_packages/completions/` | Codex has declared the package ready for review. | Must be validated against changed files and tests. |
| Git diff | Local branch | Shows implementation and documentation changes. | Diff alone cannot prove Codex is finished. |
| Test output | Terminal logs and `tests_run` field | Shows what Codex claims it verified. | The record is self-reported unless logs are retained externally. |
| Work-package deliverables | Pending package text | Defines expected artifacts. | Requires human or automated comparison. |
| Pull request metadata | PR tool or Git provider | Useful review container after branch push. | Not required for local completion and must not replace Steward approval. |
| Future Codex API status | Approved runtime adapter | Could provide task lifecycle events. | Must be optional and cannot require Enterprise-only access. |

## Detection Algorithm

Local automation should follow this order:

1. Determine the target work-package id, for example `WP-0032`.
2. Look for `collaboration/work_packages/completions/WP-0032_codex_done.json`.
3. Parse and validate the standard fields.
4. Require `codex_status` to be done/completed and `ready_for_ca_review` to be true.
5. Compare `files_changed` against the package deliverables and current Git diff.
6. Surface `tests_run` and `known_limitations` to the reviewer.
7. Mark the package as `locally_complete_pending_review` only after the record validates.
8. Preserve Steward or Chief Architect approval before merge.

## Helper Support

The helper module `estate.core.codex_completion` provides local consumption of completion records. It can:

- Build the standard completion-record path for a work-package id.
- Load a completion JSON file.
- Validate required fields and done/readiness state.
- List completion records in the completions directory.
- Format a human-readable completion status summary.

The helper intentionally does not merge branches, approve work, call GitHub Enterprise APIs, or make completion depend on GitHub merged state.

## Future Codex API Integration

If a future Codex API or runtime event stream is approved, it should be added as an optional secondary signal. The adapter should map remote lifecycle events into the same local model:

- `running`
- `changes_available`
- `completion_record_written`
- `locally_complete_pending_review`
- `reviewed`
- `approved_for_merge`
- `merged`

The local completion record remains the compatibility boundary so non-Enterprise and offline workflows continue to work.

## Steward Approval Boundary

A valid completion record authorizes review only. It does not authorize merge by itself. Merge remains gated by Steward or Chief Architect approval, existing promotion rules, and any Class A review requirements attached to the work package.
