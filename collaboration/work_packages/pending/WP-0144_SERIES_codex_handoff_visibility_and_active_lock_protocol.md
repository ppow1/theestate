# SERIES TASK WP-0144 - Codex Handoff Visibility and Active Lock Protocol

## Codex Command

Read collaboration/work_packages/pending/WP-0144_SERIES_codex_handoff_visibility_and_active_lock_protocol.md and do exactly what it says.

## Mode

SERIES

## Problem

The Estate currently has no reliable local source of truth showing whether a pending work package has already been handed to Codex and is actively being worked.

This causes a dangerous workflow failure:

- a work package is written to `collaboration/work_packages/pending/`;
- the Steward or assistant hands it to Codex;
- the Steward often sends the Codex handoff immediately after receiving it;
- new evidence arrives while Codex is running;
- GitHub search may report incorrectly, incompletely, or with delay;
- because GitHub search cannot be trusted as the first-layer source of truth for active Codex work, the assistant may incorrectly update the same pending file;
- Codex may already be working from the old content;
- the repository now has a moving target and the active worker loses a stable assignment contract.

This happened around WP-0141 and WP-0143. The root problem is not only assistant discipline. The Estate lacks an active handoff/lock protocol that does not depend on GitHub search.

## Steward Operating Rule

The Steward's normal operating principle is:

```text
Once a Codex handoff prompt is provided, the Steward tries to hand it to Codex as quickly as possible unless a problem is seen directly in the handoff.
```

Therefore, after a handoff prompt has been given, assistants must assume the work package may already be running unless the Steward explicitly says it has not been handed to Codex.

## Architectural Principle

A work package handed to Codex must become immutable for that run.

If additional evidence arrives after handoff, it must be captured in a new numbered work package, an addendum file, or an explicit follow-up package. Do not edit the active work package out from under Codex.

GitHub search is not an acceptable source of truth for determining that a Codex task is not active.

## Required Outcome

Create an Estate-native Codex handoff visibility and active-lock protocol so the Steward and assistants can determine whether a work package is safe to update before modifying it.

## Requirements

### 1. Active Codex Handoff Ledger

Create a local artifact that records Codex handoffs.

Suggested path:

```text
collaboration/work_packages/codex_handoffs.json
```

or another existing appropriate collaboration/runtime location if one already exists.

Each entry should include:

- work package id;
- work package path;
- handoff command text;
- handed off by;
- handoff timestamp;
- state: `prepared`, `handoff_prompt_given`, `handed_to_codex`, `codex_running`, `codex_pr_opened`, `merged`, `superseded`, `abandoned`;
- related Codex task URL if available;
- related branch if available;
- related PR number if available;
- related merge commit if available;
- superseded by work package id if applicable;
- notes.

### 2. Active Lock Marker

When a work package handoff prompt is given, mark the package as active/locked or at least handoff-risk.

Possible implementation choices:

- update the handoff ledger only;
- create a sidecar lock file;
- move or copy active packages into an active/claimed directory;
- reuse an existing work-package claimed/open/completion subsystem if available.

Do not invent redundant machinery if an existing Estate mechanism already supports this.

The visible rule must be:

```text
If a work package is active/locked or handoff-risk, do not edit it. Create the next numbered work package instead unless the Steward explicitly confirms it was not handed to Codex.
```

### 3. CLI / Command Support

Add or extend CLI commands to support the workflow.

At minimum provide commands equivalent to:

```text
estate work-packages codex-handoff <work-package-path>
estate work-packages codex-status
estate work-packages codex-locks
estate work-packages codex-supersede <old-wp-id> <new-wp-id>
```

Use existing CLI structure and naming if different conventions already exist.

The handoff command should print the exact Codex prompt the Steward should paste:

```text
Read collaboration/work_packages/pending/<filename>.md and do exactly what it says.
```

It should also record that the prompt was issued so later assistants know the file is not safe to mutate.

### 4. Update Assistant/Steward Workflow Documentation

Document the new rule in the relevant Estate operations documentation.

The documentation must state:

- never update a work package after its Codex handoff prompt has been given unless the Steward explicitly confirms it has not been handed to Codex;
- check the active handoff ledger before editing a pending work package;
- if a package may already be running, create the next numbered package;
- new evidence after handoff becomes a follow-up package, not an in-place edit;
- GitHub PR/search results are not sufficient to prove Codex is not already running;
- GitHub search may return false negatives and must not be treated as authoritative for active Codex task state.

### 5. Command Center Visibility

Expose active Codex handoffs in the Office of the Steward Command Center or existing Work Packages panel.

At minimum show:

- active Codex handoffs;
- locked or handoff-risk work package ids;
- related PRs when known;
- packages safe to edit;
- packages that require follow-up instead of mutation;
- packages superseded by later evidence.

This should be read-only unless an existing governed action supports state changes.

### 6. Guardrails Against Accidental Updates

If practical, add a validation check that warns when a pending work package with active handoff state is modified.

Options include:

- validation command warning;
- work-package validation failure;
- CLI refusal unless `--force` is explicitly used;
- report-only warning if strict enforcement would disrupt current operations.

Do not block emergency repair workflows completely, but require the operator to make the override explicit.

### 7. Follow-Up Package Rule

Add an explicit rule for new evidence after handoff:

```text
If new evidence arrives after the handoff prompt was given, create the next numbered work package. Do not edit the active work package.
```

The next work package should state:

- which package it supersedes or extends;
- what new evidence arrived;
- why the prior package must not be edited;
- what Codex should do differently.

### 8. Tests

Add tests proving:

1. A handoff record can be created.
2. Handoff record stores work package id, path, timestamp, state, and command text.
3. Active/locked or handoff-risk packages are listed.
4. Superseding an active package points to the new work package.
5. Command Center or Work Packages panel renders active Codex handoffs.
6. Validation warns or fails when an active locked work package is modified.
7. New evidence workflow can create a new numbered package without mutating the active one.
8. Existing work-package validation remains passing.
9. GitHub search is not used as the authority for whether a Codex task is active.

## Files To Inspect

Inspect existing work-package and collaboration systems before adding new structure:

- `collaboration/work_packages/`
- `operations/work_packages/`
- `runtime/work_packages/`
- `src/estate/cli/`
- work-package validation modules/tests
- Steward Command Center work-package panel code

## Required Report Artifacts

Create:

```text
operations/work_packages/WP-0144_codex_handoff_visibility_and_active_lock_protocol_report.md
runtime/work_packages/WP-0144_codex_handoff_visibility_and_active_lock_protocol_report.json
collaboration/work_packages/completions/WP-0144_codex_done.json
```

The report must include:

- root cause;
- chosen artifact paths;
- new or reused lock/handoff mechanism;
- CLI commands added or updated;
- Command Center visibility;
- guardrail behavior;
- documentation updated;
- how false-negative GitHub search is avoided;
- tests run;
- remaining limitations.

## Acceptance Criteria

WP-0144 is complete when the Estate has a visible local source of truth for Codex handoffs, active or handoff-risk work packages are clearly locked against mutation, the Steward can see which Codex packages are active, assistants have a documented rule to create a new package instead of editing an active one, and tests protect against repeating the WP-0141/WP-0143 active-file update failure.

## Merge Class

Class A. Escalate if implementation changes constitutional work-package semantics, deletes active packages, rewrites historical completion artifacts, or introduces external/cloud dependency for Codex task visibility.
