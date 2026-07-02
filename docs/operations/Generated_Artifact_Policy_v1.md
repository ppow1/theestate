# Generated Artifact Policy v1

Status: Active Policy
Owner: Chief Architect / Alfred Operations
Classification: Estate Internal
Introduced By: WP-0026
Date: 2026-07-02

## Purpose

The Estate produces both authored institutional records and generated operational views. This policy defines how workers should distinguish authoritative source artifacts from generated projections, local runtime state, committed generated summaries, and institutional evidence.

This policy documents existing Estate principles. It does not redesign artifact storage, promote generated files into source-of-truth authority, or change the approval rules for Local Only artifacts.

## Core Rule

Generated artifacts may help workers understand current operating state, but they must not override the authored records, registries, message files, work packages, review records, promotion records, or other authoritative institutional files from which they were derived.

When a generated artifact disagrees with an authoritative source artifact, workers must treat the disagreement as a validation issue and inspect the source artifact before taking action.

## Artifact Classes

### 1. Authoritative Source Artifacts

Authoritative source artifacts are authored records that define institutional intent, identity, policy, contracts, or accepted decisions. They are the source material from which generated projections may be built.

Examples:

- `collaboration/messages/*.json` — authoritative message records. Mailbox indexes, inbox summaries, and status summaries are views over these files.
- `collaboration/work_packages/pending/*.md` — authored operational contracts for proposed or queued work.
- `collaboration/work_packages/open/*.md` — authored or accepted work contracts that are available for execution.
- `data/registry/*.json` — registry source files for identity, routing, capability, and related institutional data.
- `docs/**/*.md` — authored policy, architecture, onboarding, operations, governance, and protocol documents unless a document explicitly identifies itself as generated.
- `operations/boards/*.md` — approved Operations Board surfaces when manually maintained or intentionally committed as operational board files.

Worker expectations:

1. Prefer source artifacts for final decisions.
2. Cite or inspect source artifacts when generated summaries are incomplete, stale, or contradictory.
3. Do not rewrite source artifacts merely to match generated output.

### 2. Generated Operational Projections

Generated operational projections are derived views created by tooling, adapters, summaries, dashboards, validation runners, or reports. They are useful for situational awareness and review, but they are not independent authority.

Examples:

- `collaboration/mailboxes/index.json` — generated mailbox index over message and mailbox data.
- `collaboration/status/*.json` — generated or refreshed collaboration status projections such as inbox and event summaries.
- `operations/updates/check_updates_latest.md` — generated Check for Updates surface.
- `operations/mailboxes/synchronization_duty.md` — generated mailbox synchronization duty view.
- `operations/validation/*.md` and `runtime/validation/*.json` — validation reports and machine-readable validation results.
- `operations/capabilities/lifecycle_status.md` — generated capability lifecycle reporting unless explicitly promoted by a review record.
- `operations/dependencies/dependency_graph.md` and `runtime/dependencies/dependency_graph.json` — generated dependency views.
- `operations/alfred/operational_briefing.md` and `runtime/alfred/operational_briefing.json` — generated Alfred briefing outputs.
- `operations/board/latest.md` and `runtime/operations/*.json` — generated Operations Board integration outputs.
- `operations/steward/dashboard.md` — generated Steward-facing dashboard view.

Worker expectations:

1. Use projections to find what changed, what may be blocked, and which source files require inspection.
2. Regenerate projections using the appropriate local command before relying on them for current operational review when freshness matters.
3. Treat projection/source disagreement as a warning, not as authority to overwrite source files.

### 3. Local-Only Runtime Artifacts

Local-only runtime artifacts are mutable execution state, private intermediate data, local caches, job results, prompts, generated media, and runtime logs. They default to Local Only unless explicitly classified and promoted through the applicable promotion process.

Examples:

- `runtime/alfred/jobs/`
- `runtime/alfred/requests/`
- `runtime/audit/`
- `runtime/discovery/`
- `runtime/services/`
- `runtime/collaboration/events/events.jsonl`
- `runtime/collaboration/events/latest.json`
- `runtime/collaboration/outbox/`
- `runtime/collaboration/dead_letter/`
- generated prompts, prompt history, generated media, private task artifacts, and local caches

Worker expectations:

1. Do not commit runtime artifacts unless an existing policy, work package, or promotion record explicitly says the specific artifact is repository-visible.
2. Do not publish private Local Only artifact details by copying them into committed summaries.
3. Preserve local runtime state when it is needed for debugging, but do not treat it as institutional memory by default.

### 4. Committed Generated Summaries

Some generated summaries are intentionally committed because they give workers and the Steward repository-visible operational awareness. Committing a generated summary does not make it source of truth.

Examples:

- `collaboration/status/event_summary.json`
- `collaboration/status/worker_inbox_summary.json`
- `collaboration/mailboxes/index.json`
- `operations/validation/local_operational_validation_run.md`
- `operations/validation/operational_validation_report.md`
- `operations/updates/check_updates_latest.md`
- `operations/steward/dashboard.md`
- `operations/board/latest.md`

Worker expectations:

1. Commit generated summaries only when they are expected repository-visible operational views or when the work package requests them.
2. Include enough context in completion notes for reviewers to understand how the summary was produced.
3. If a committed summary is stale, regenerate it or document the limitation rather than editing the summary by hand to appear current.

### 5. Institutional Evidence

Institutional evidence records that work occurred, was reviewed, or was accepted. Evidence may summarize generated checks, but its institutional value comes from being an authored or accepted record of completion, review, validation, or promotion.

Examples:

- `collaboration/work_packages/completions/*.json` — completion records, including Codex completion signals.
- `collaboration/work_packages/reviews/*` — review artifacts where present.
- `operations/history/*.md` — operational history records.
- promotion records defined by collaboration or promotion workflow documentation.
- explicit validation records that a reviewer accepts as evidence for a capability lifecycle state.

Worker expectations:

1. Preserve evidence records as traceability artifacts.
2. Do not treat a completion artifact as proof that every underlying source artifact is correct; it is proof that the worker declared completion and provided review context.
3. Reviewers should use evidence records alongside source files, generated projections, tests, and Git history.

### 6. Dashboards and Board Views

Dashboards and board integrations are operational visibility surfaces. They are designed to be readable quickly and may be generated, manually maintained, or a mix depending on the specific file.

Classifications:

- `operations/boards/*.md` — approved operational board surfaces. Existing Operations Board documentation treats these as operational v1 assets and the board as a visibility surface, not a replacement for the Collaboration Layer or other source records.
- `operations/board/latest.md` — generated board integration snapshot.
- `operations/steward/dashboard.md` — generated operational dashboard.
- `runtime/operations/*.json` — machine-readable runtime projections for operations integration.

Worker expectations:

1. Use dashboards and board views for orientation.
2. Confirm source artifacts before making irreversible or authority-sensitive changes.
3. Keep dashboards concise; do not embed private Local Only runtime details.

## Required Path Classification Registry

| Path or Pattern | Classification | Commit Expectation | Source-of-Truth Rule |
|---|---|---|---|
| `collaboration/messages/*.json` | Authoritative message records | Commit when authored/accepted | Source of truth for individual messages |
| `collaboration/mailboxes/index.json` | Generated mailbox projection | May be committed as operational view | Derived from message and registry sources |
| `collaboration/status/*.json` | Generated status projections | May be committed when repository-visible | Derived view, not authority |
| `collaboration/work_packages/pending/*.md` | Authored operational contracts | Commit when created/updated | Source for requested work scope |
| `collaboration/work_packages/open/*.md` | Authored operational contracts | Commit when created/updated | Source for open work scope |
| `collaboration/work_packages/completions/*.json` | Institutional evidence | Commit at completion | Evidence of completion declaration |
| `collaboration/work_packages/reviews/*` | Institutional evidence | Commit when review is recorded | Evidence of review, not automatic promotion |
| `operations/boards/*.md` | Operations Board operational views/assets | Commit approved board updates | Visibility surface; does not replace source records |
| `operations/board/latest.md` | Generated board projection | May be committed when refreshed | Derived view |
| `operations/steward/dashboard.md` | Generated dashboard | May be committed when refreshed | Derived view |
| `operations/alfred/operational_briefing.md` | Generated briefing projection | May be committed when appropriate | Derived view |
| `operations/validation/*.md` | Generated validation summaries | May be committed as evidence-supporting views | Derived from validation runs |
| `runtime/**/*.json` and `runtime/**` | Local-only runtime artifacts unless explicitly promoted | Do not commit by default | Mutable local state, not institutional source |
| `docs/**/*.md` | Authored institutional documents unless explicitly generated | Commit when intentionally authored | Source for policy/protocol/operations guidance |
| `data/registry/*.json` | Authoritative registry source files | Commit intentional registry changes | Source for registry-backed identity/routing/capability data |

## Regeneration Expectations

Workers should regenerate generated projections when:

1. The work package asks for refreshed operational reports.
2. Source artifacts that feed the projection changed.
3. A reviewer needs current operational state.
4. A generated projection appears stale, inconsistent, or missing expected records.

Regeneration should use existing Estate commands or documented scripts. Do not hand-edit generated outputs unless the owning documentation explicitly permits manual maintenance.

## Review Expectations

Reviewers should check generated artifacts for consistency, not authority. A good review asks:

1. Which source artifacts produced this projection?
2. Was the projection regenerated after relevant source changes?
3. Does the projection expose any Local Only or private material that should not be committed?
4. Does the completion record identify files changed, checks run, known limitations, and readiness for CA review?
5. Are any disagreements between source files and generated views documented as warnings?

## Never Treat These as Source of Truth

The following must never be treated as independent source of truth:

- conversation memory or uncommitted chat context
- generated summaries that cannot be traced to source artifacts
- stale dashboards or status pages
- local runtime caches and mutable job state
- prompts, prompt history, generated media, or intermediate artifacts
- mailbox/status summaries when individual `collaboration/messages/*.json` files disagree
- validation reports when underlying source files or tests contradict them
- board snapshots when work packages, messages, or promotion records disagree

## Escalation

If workers cannot determine whether an artifact is source, projection, runtime state, committed summary, or institutional evidence, they should classify it conservatively as Local Only or generated projection, document the uncertainty, and request Chief Architect review before promotion or authority-sensitive use.
