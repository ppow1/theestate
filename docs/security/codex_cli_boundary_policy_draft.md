# Codex CLI Boundary Policy Draft

Status: Draft for Ingrid Review
Owner: Ingrid / Privacy and Boundary Office
Operational Consumers: Alfred, Helen, Chief Architects, Codex Bridge implementers
Classification: Estate Internal
Created: 2026-07-07

## Purpose

This draft defines the initial security boundary for using Codex CLI as an Estate execution provider.

It is not an approval for unrestricted Codex access.

The safe default is:

```text
Codex may receive only the minimum repository context required for an approved task, may write only to explicit allowed paths, and must produce auditable output before any result is promoted back into the Estate.
```

## Current Risk Statement

The discovery session proved that Codex CLI can be invoked programmatically through `codex exec`. That creates a useful execution bridge and a new boundary crossing:

```text
local Estate context -> Codex CLI prompt/model/provider -> generated output -> local Estate files
```

The risk is not only file writes. The prompt itself can export repository content, local runtime state, credentials, resident information, or internal policy context to an external model or cloud task.

## Operating Posture

| Category | Posture |
| --- | --- |
| Immediate safe use | Read-only characterization, docs-only planning, local-provider testing, and explicit small prompts with no sensitive runtime state |
| Experimental use | Approved work-package execution through `codex exec` with JSONL capture, sandboxing, write allowlists, and human review |
| Prohibited or unapproved use | Unrestricted `A:\theestate` dispatch, cloud apply automation, credential exposure, resident-private data exposure, and `danger-full-access` automation |

## Boundary Matrix

| Estate area | Codex read default | Codex write default | Outbound prompt/export default | Notes |
| --- | --- | --- | --- | --- |
| `README.md`, `AI_START_HERE.md`, `AI_HINTS.md` | Allowed for onboarding tasks | No direct write unless package requires it | Allowed | Safe orientation material, still cite task need |
| Authored governance docs under `docs/governance/` | Allowed when task requires | Review required | Allowed with task scope | Governance edits require Chief Architect or Steward review |
| Authored architecture/docs under `docs/architecture/`, `docs/integration/`, `docs/security/` | Allowed | Allowed for approved docs packages | Allowed with task scope | Security docs require Ingrid review before becoming policy |
| Source code under `src/` and tests under `tests/` | Allowed for implementation packages | Allowed only with explicit work package | Allowed with task scope | Require test evidence and completion receipt |
| Work packages under `collaboration/work_packages/` and `docs/governance/workers/` | Allowed | Allowed only for package authoring/completion tasks | Allowed | Do not silently change scope or authority |
| Completion receipts under `collaboration/work_packages/completions/` | Read allowed | Write allowed only as final implementation receipt | Allowed | Receipt is self-report, not approval |
| `runtime/` | Denied by default | Denied by default | Denied by default | Local runtime state is not source and may be sensitive |
| Live operations projections and dashboards | Review required | Denied by default | Review required | See repository boundary policy for generated/local state |
| Resident conversations, approvals, attachments, private local state | Denied | Denied | Denied | Requires explicit Ingrid/Steward approval |
| Credentials, `.env`, auth files, `CODEX_HOME`, API keys, tokens | Denied | Denied | Denied | Never include in prompts or logs |
| `.git/` internals | Read only through normal git commands | Denied | Do not export raw internals | Git status/diff/log are acceptable when task requires |
| `estate_ledger/ledger.md` and `development/devlog.md` | Read allowed if task requires | Denied by default | Review required | History repair must follow approved queue/drain workflow |
| Cloud task diffs | Read-only inspection only | `apply` denied by default | Review required | Cloud apply is unapproved until policy is finalized |

## Approved Initial Execution Profiles

### Profile 1: Characterization Read-Only

Use for capability testing and diagnostics.

```powershell
codex --ask-for-approval never exec --sandbox read-only --color never --ephemeral --json -
```

Rules:

- No file writes expected.
- Prompt must not include secrets or private runtime data.
- Capture stdout, stderr, exit code, provider, model, working directory, and timestamps.

### Profile 2: Documentation Workspace Write

Use for approved documentation packages.

Allowed write roots should be explicit, for example:

```text
docs/integration/
docs/security/
docs/architecture/
observations/
docs/governance/workers/
```

Rules:

- Use `workspace-write`, not `danger-full-access`.
- Do not modify runtime state.
- Do not create or modify credentials.
- Human review required before policy documents become authoritative.

### Profile 3: Implementation Workspace Write

Use only for an approved work package with clear scope.

Rules:

- Work package must list allowed files or allowed directories.
- Bridge must capture diff and test evidence.
- Completion receipt does not approve merge.
- Steward, Chief Architect, or delegated reviewer must approve promotion.

## Prohibited Until Further Approval

The following are not approved for routine automation:

- `--dangerously-bypass-approvals-and-sandbox`
- `--sandbox danger-full-access`
- broad prompt export of all `A:\theestate`
- prompts containing secrets, auth files, local credentials, resident-private data, or live runtime state
- automatic `codex cloud apply`
- automatic local `git apply` from Codex output
- cloud execution for sensitive or private work packages
- multi-seat profile automation without profile inventory and audit labeling
- silent retry loops that burn seat usage without budget checks

## Prompt Boundary Requirements

Every bridge request should record:

- request id
- work package id or reason
- requested provider and model
- `CODEX_HOME` profile label, not secret path contents
- working directory
- sandbox mode
- approval mode
- allowed read paths
- allowed write paths
- prompt source path
- prompt hash
- classification
- whether cloud execution is allowed

The bridge should store prompt text locally by default. If a prompt must be committed as evidence, it must be reviewed for sensitive content first.

## Output Boundary Requirements

Every bridge result should record:

- exit code
- stdout hash and sanitized excerpt
- stderr hash and sanitized excerpt
- JSONL event summary when applicable
- token usage when available
- files changed
- tests run
- known limitations
- classification
- promotion decision

Raw output should remain local runtime data unless deliberately promoted as evidence.

## Cloud Boundary

Codex Cloud is a stronger external crossing than local `codex exec`.

Initial approved posture:

| Cloud command | Draft posture |
| --- | --- |
| `codex cloud list` | Experimental read-only after sign-in |
| `codex cloud status <task>` | Experimental read-only after sign-in |
| `codex cloud diff <task>` | Experimental read-only after sign-in and task classification |
| `codex cloud exec --env <env>` | Requires explicit environment approval and task classification |
| `codex cloud apply <task>` | Prohibited for automation until Ingrid approves diff review and local patch policy |

## Multi-Seat Boundary

`CODEX_HOME` path isolation is structurally supported by the CLI, but authenticated multi-seat behavior is not yet proven.

Before routine use, each profile needs:

- a stable profile label
- a dedicated `CODEX_HOME`
- confirmed auth identity
- owner/account record
- allowed task classes
- usage-status observation method
- audit log path
- revocation procedure

## Unknowns Requiring Ingrid Review

- Whether `/status` can be captured non-interactively.
- Whether ChatGPT Business seat usage can be parsed without TUI observation.
- Whether multiple authenticated `CODEX_HOME` profiles can run concurrently.
- Whether cloud task ids map cleanly to browser Codex tasks.
- Whether cloud diffs can be safely inspected without applying.
- What repository content is considered safe to include in external prompts by default.

## Draft Decision

Until this policy is approved, Codex CLI should be treated as:

```text
approved for bounded characterization and explicitly scoped documentation work,
experimental for implementation work,
not approved for unrestricted autonomous execution or cloud apply.
```
