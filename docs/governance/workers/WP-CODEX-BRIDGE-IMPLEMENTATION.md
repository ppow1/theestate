# WP-CODEX-BRIDGE-IMPLEMENTATION - Production Codex Bridge Implementation

Status: Proposed
Priority: High
Owner: Chief Architect / Steward
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Alfred, Helen, future Operations Manager, local workers, Codex workers
Classification: Estate Internal
Created: 2026-07-07

## Codex Command

Read this work package and do exactly what it says.

Do not implement unrestricted autonomous Codex execution.

Do not use Codex Cloud apply.

## Mission

Implement the first production Codex Bridge as a conservative local execution adapter.

The bridge must read an approved prompt or work package, invoke Codex CLI with explicit boundaries, capture structured results, normalize output, write local audit evidence, and return a reviewable result without relying on conversation memory.

## Background

The Estate proved that Codex CLI can be invoked programmatically through stdin/stdout during the 2026-07-07 discovery session.

The characterization package then documented CLI behavior, security boundaries, and provider mapping.

Required source documents:

```text
observations/codex_cli_bridge_discovery_2026-07-07.md
observations/codex_cli_bridge_characterization_results.md
docs/integration/codex_cli_capability_matrix.md
docs/security/codex_cli_boundary_policy_draft.md
docs/architecture/execution_provider_codex_cli_mapping.md
docs/collaboration/Local_Execution_Adapter_Protocol_v1.md
docs/security/Repository_Boundary_and_Local_Runtime_State_v1.md
docs/operations/Codex_Task_Template_Standard_v1.md
```

## Scope

Build a local bridge implementation that supports:

1. A request model for invoking Codex CLI.
2. A result model for captured execution output.
3. A command runner for `codex exec`.
4. JSONL parsing for `--json` output.
5. Text-mode fallback parsing.
6. Output cleanup for ANSI/control characters.
7. UTF-8 normalization and CP437 mojibake recovery.
8. Token usage extraction when available.
9. `CODEX_HOME` profile labeling.
10. Read-only default sandboxing.
11. Workspace-write execution only with explicit allowed paths.
12. Local audit logging under `runtime/codex_bridge/`.
13. A CLI command or documented entry point for running a bridge request.
14. Tests for parsing, cleanup, request validation, and denied boundary cases.

## Out Of Scope

This package must not:

- implement Codex Cloud apply
- implement unrestricted cloud task dispatch
- implement multi-seat auto-rotation
- store credentials in the repository
- read or write `.env`, auth files, or `CODEX_HOME` secrets
- bypass sandboxing
- modify Alfred, Helen, Ingrid, or Office authority
- create a new Office
- commit live runtime logs
- require GitHub as the source of local execution truth

## Required Behavior

### Request Validation

The bridge must reject a request when:

- classification is missing
- prompt source does not exist
- prompt source is outside allowed read paths
- write mode is requested without allowed write paths
- requested write paths are too broad
- `danger-full-access` is requested
- bypass flags are requested
- cloud apply is requested
- provider profile is unknown

### Command Construction

Default read-only command shape:

```powershell
codex --ask-for-approval never exec --sandbox read-only --color never --ephemeral --json -
```

Workspace-write command shape may omit `--ephemeral` only when session persistence is explicitly required by the request.

The bridge must place top-level options before `exec`.

### Output Capture

The bridge must capture:

- stdout
- stderr
- exit code
- started timestamp
- finished timestamp
- duration
- command arguments with secrets redacted
- cwd
- provider
- model
- `CODEX_HOME` profile label

### Output Parsing

The bridge must prefer JSONL mode and parse:

- `thread.started`
- `turn.started`
- `item.completed`
- final `agent_message`
- `turn.completed.usage`
- `turn.failed`
- `error`

Text fallback must treat stdout as the final assistant message and stderr as telemetry. Stderr alone must not be treated as failure when exit code is `0`.

### Output Normalization

The bridge must:

- strip ANSI escape sequences
- strip non-printing terminal control characters
- preserve line breaks
- force UTF-8 where possible
- recover CP437-decoded UTF-8 mojibake for known patterns
- keep raw-output hashes for audit

### Audit Logging

Write local runtime audit records under:

```text
runtime/codex_bridge/
```

The repository already ignores `runtime/`, so these logs remain local unless a deliberate evidence artifact is created and classified.

Each audit record must include:

- request id
- work package id, if any
- request classification
- provider and model
- profile label
- sandbox mode
- allowed paths
- prompt hash
- command run
- exit code
- usage
- result summary
- changed files
- tests run
- known limitations
- promotion recommendation

## Required Artifacts

Implementation should create or update only paths justified by the existing codebase. Expected artifacts include:

```text
src/estate/core/codex_bridge.py
tests/test_codex_bridge.py
docs/integration/codex_bridge_usage.md
```

If the existing CLI structure supports it cleanly, add an Estate CLI command for bridge execution. If not, document the callable Python entry point and defer CLI wiring to a follow-up package.

## Test Requirements

Add tests that cover:

- request validation accepts read-only allowed requests
- request validation rejects missing classification
- request validation rejects `danger-full-access`
- request validation rejects cloud apply
- JSONL parser extracts final message and token usage
- JSONL parser records failed turns
- text parser extracts stdout final message and stderr token usage
- ANSI/control cleanup
- CP437 mojibake recovery for `IΓÇÖm`
- audit record redacts secrets and does not include raw credentials

Tests must not require live OpenAI network access.

## Validation Recipe Requirement

If the Estate validation framework supports work-package-specific recipes, add a local validation recipe for this package.

The validation must be local-first and must not call OpenAI or Codex Cloud.

At minimum, document the commands:

```powershell
pytest tests/test_codex_bridge.py
python -m estate.cli.main validation-production-readiness --json
```

If a validation recipe is not added, the completion receipt must explicitly state why it is not applicable.

## Demonstration Requirements

The implementation report must include:

- a dry-run request validation example
- a parser-only JSONL fixture example
- a local-provider smoke test if Ollama is available
- an OpenAI-backed smoke test only if credentials and network are available
- a clear statement when live Codex execution was skipped

## Safety And Authority Constraints

- Ingrid owns final boundary approval.
- Steward remains final authority for reserved decisions.
- Alfred may coordinate routing but does not own boundary policy.
- Helen may provision worker profiles but does not approve sensitive data export.
- Completion receipts authorize review only, not merge.
- Runtime logs remain local unless deliberately promoted.

## Acceptance Criteria

This package is complete when:

- a local Codex Bridge module exists
- request and result models are implemented
- JSONL and text parsing are tested
- output cleanup and encoding normalization are tested
- denied boundary cases are tested
- audit logging writes under `runtime/codex_bridge/`
- no tests require live network access
- documentation explains how to run the bridge
- prohibited modes are blocked by code, not only by comments
- a completion receipt exists if this package is executed by Codex

## Known Limitations To Preserve

The implementation must explicitly preserve these unknowns until separately resolved:

- non-interactive `/status` automation is unknown
- authenticated multi-seat concurrency is unknown
- Codex Cloud task lifecycle is unknown
- Codex Cloud apply is unapproved
- OpenAI-backed JSONL usage shape needs authenticated verification

## Completion Signal

If implemented by Codex, create:

```text
collaboration/work_packages/completions/WP-CODEX-BRIDGE-IMPLEMENTATION_codex_done.json
```

The receipt must include files changed, tests run, known limitations, boundary decisions, and whether any live Codex/OpenAI calls were skipped.
