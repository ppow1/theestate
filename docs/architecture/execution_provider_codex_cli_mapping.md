# Execution Provider Mapping: Codex CLI

Status: Draft
Owner: Chief Architect
Boundary Authority: Ingrid / Privacy and Boundary Office
Classification: Estate Internal
Created: 2026-07-07

## Purpose

This document maps generic Estate execution-provider concepts onto the installed Codex CLI command surface.

The goal is to let Alfred, a future orchestrator, or a LEAP-style adapter treat Codex CLI as one execution provider without hard-coding Codex-specific behavior throughout the Estate.

## Provider Modes

| Mode | Command family | Current status |
| --- | --- | --- |
| OpenAI-backed local exec | `codex exec` | Proven in prior discovery; blocked in current sandbox by missing credentials and network restrictions |
| Local OSS exec through Codex CLI | `codex exec --oss --local-provider ollama` | Proven for pipe mechanics with Ollama |
| Codex Cloud | `codex cloud ...` | Command surface present; live task lifecycle untested in current unsigned shell |

## Generic Contract Mapping

| Generic provider concept | Codex CLI mapping | Evidence / limitation |
| --- | --- | --- |
| `capabilities` | `codex --help`, `codex exec --help`, `codex cloud --help`, `codex doctor --json` | Help commands are available locally |
| `health` | `codex doctor --json` | Reports auth, config, install, git, network, sandbox, state, terminal |
| `submit` synchronous | `codex exec [prompt]` or `prompt | codex exec -` | Runs to completion and returns process exit code |
| `submit` asynchronous/cloud | `codex cloud exec --env <ENV_ID> [QUERY]` | Requires environment id; no live task submitted in this run |
| `status` local exec | Process state, JSONL events, exit code | No separate local task id for basic `exec` |
| `status` cloud | `codex cloud status <TASK_ID>` | Requires sign-in and task id |
| `status` seat/fuel | Interactive TUI `/status` | Prior discovery only; no non-interactive command found |
| `result` text mode | stdout final assistant message | Proven with local provider; prior discovery proved OpenAI provider |
| `result` file | `--output-last-message <FILE>` | Proven with local provider |
| `result` JSONL | `--json` event stream on stdout | Proven with local provider and failure path |
| `usage` | JSONL `turn.completed.usage`; text-mode `tokens used` on stderr | Proven with local provider; OpenAI success path untested here |
| `logs` | stderr plus JSONL events | stderr contains headers, warnings, transcript echoes, token usage, and transport diagnostics |
| `diff` local | Local `git diff` after a workspace-write run | Bridge should capture separately |
| `diff` cloud | `codex cloud diff <TASK_ID>` | Requires sign-in and task id |
| `apply` local | Human-reviewed patch application or `codex apply` | Not approved for bridge v1 automation |
| `apply` cloud | `codex cloud apply <TASK_ID>` | Prohibited for automation until boundary policy is approved |
| `cancel` local | Terminate child process | No first-class local cancellation command observed |
| `cancel` cloud | Unknown | No cloud cancel command observed in help |
| `estimate_cost` | Not directly exposed | Bridge can estimate only from prior usage and model/profile policy |
| `estimate_time` | Not directly exposed | Bridge can measure historical durations |

## Recommended Bridge v1 Architecture

```text
Work package / request
-> boundary classifier
-> prompt builder
-> provider selector
-> Codex CLI command runner
-> stream capture
-> JSONL parser / text fallback parser
-> output normalizer
-> result classifier
-> audit log
-> optional artifact writer
-> human review / promotion
```

## Request Model

Minimum request fields:

| Field | Purpose |
| --- | --- |
| `request_id` | Stable bridge request id |
| `work_package_id` | Link to Estate work package, if any |
| `requested_by` | Human or office initiating request |
| `provider` | `codex-cli-openai`, `codex-cli-ollama`, or `codex-cloud` |
| `model` | Requested model name |
| `codex_home_profile` | Profile label, not secret contents |
| `cwd` | Working directory |
| `sandbox` | `read-only` or `workspace-write` for approved tasks |
| `approval_policy` | Usually `never` for automation |
| `allowed_read_paths` | Explicit read boundary |
| `allowed_write_paths` | Explicit write boundary |
| `prompt_source` | Work package or generated prompt path |
| `classification` | Boundary classification |
| `cloud_allowed` | Boolean |
| `expected_outputs` | Files, stdout shape, or completion receipt |
| `validation_commands` | Commands to run after execution |

## Result Model

Minimum result fields:

| Field | Purpose |
| --- | --- |
| `request_id` | Link to request |
| `status` | `succeeded`, `failed`, `blocked`, `policy_denied`, or `needs_review` |
| `started_at` / `finished_at` | Timing |
| `command` | Redacted command line |
| `exit_code` | Process exit |
| `stdout_summary` | Sanitized summary |
| `stderr_summary` | Sanitized summary |
| `stdout_hash` / `stderr_hash` | Raw-output audit references |
| `json_events` | Event counts and final event types |
| `usage` | Token usage when available |
| `files_changed` | Git diff summary |
| `tests_run` | Validation evidence |
| `known_limitations` | Explicit unresolved items |
| `classification` | Output classification |
| `promotion_decision` | `local_only`, `evidence_approved`, or `blocked` |

## Command Templates

Read-only OpenAI-backed exec:

```powershell
$prompt | codex --ask-for-approval never exec --sandbox read-only --color never --ephemeral --json -
```

Documentation or implementation exec after approval:

```powershell
$prompt | codex --ask-for-approval never exec --sandbox workspace-write --color never --json -
```

Local provider mechanics test:

```powershell
$prompt | codex --ask-for-approval never exec --oss --local-provider ollama -m qwen2.5-coder:7b --sandbox read-only --color never --ephemeral --json -
```

Cloud list, read-only:

```powershell
codex cloud list --json --limit 20
```

Cloud task submission, experimental only:

```powershell
codex cloud exec --env <ENV_ID> --branch <BRANCH> '<task prompt>'
```

Cloud apply is intentionally not part of bridge v1 automation.

## Stream Handling

Preferred path:

```text
stdout JSONL -> parse event records -> extract final agent message and usage
stderr -> operational telemetry and diagnostics
```

Fallback path:

```text
stdout text -> final assistant message
stderr text -> headers, warnings, transcript echo, tokens used
```

The bridge must not assume stderr means failure. Successful text-mode runs can include token usage and warnings on stderr.

## Boundary Hooks

The bridge should stop before dispatch when:

- classification is missing
- prompt source is outside the approved read boundary
- requested write paths are absent or too broad
- cloud execution is requested without explicit approval
- `danger-full-access` is requested
- prompt text contains obvious secret material
- `CODEX_HOME` profile is unknown

The bridge should stop after execution before promotion when:

- output classification is unknown
- generated diff touches paths outside the allowlist
- tests fail or are not run when required
- output includes secrets or private runtime data
- cloud diff is present but unreviewed

## Relationship To LEAP

Codex Bridge should follow the Local Execution Adapter Protocol lifecycle:

```text
pending -> active -> validate -> execute -> capture -> publish -> archive -> failed
```

Only the `execute` step is Codex-specific. Request validation, capture, classification, publication, and archive should stay reusable across future providers.

## Unknowns

- Non-interactive access to the interactive `/status` fuel gauge.
- Authenticated multi-seat concurrency through separate `CODEX_HOME` profiles.
- Codex Cloud task id shape, lifecycle states, and browser mapping.
- Whether `codex cloud diff` returns enough metadata for safe review without applying.
- Whether OpenAI-backed JSONL success events include the same usage shape observed with the local provider.
