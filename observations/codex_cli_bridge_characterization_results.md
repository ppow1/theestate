# Codex CLI Bridge Characterization Results

Status: Captured
Owner: Chief Architect / Steward
Classification: Estate Internal
Captured: 2026-07-07 23:34 -04:00
CLI Version Tested: codex-cli 0.142.5
Source Work Package: `docs/governance/workers/WP-CODEX-CLI-001.md`

## Summary

The 2026-07-07 discovery result remains valid as prior evidence: an authenticated shell was able to run:

```powershell
$prompt = 'Reply with exactly: hello from direct pipe'
$result = $prompt | codex exec -
```

and capture:

```text
hello from direct pipe
```

This rerun could not reproduce the OpenAI-backed direct pipe in the current shell because the shell runs under a sandboxed Codex home with no credentials and restricted network access. The rerun did characterize the installed CLI surface, stream behavior, JSONL mode, local-provider pipe behavior, file-backed prompts, encoding cleanup, `CODEX_HOME` path isolation, and blocked cloud behavior.

## Environment Observed

| Item | Observation |
| --- | --- |
| Repository | `A:\theestate` |
| CLI version | `codex-cli 0.142.5` |
| Default shell Codex home in this run | `C:\Users\CodexSandboxOffline\.codex` |
| Default shell auth status | `codex doctor --json` reported `no Codex credentials were found` |
| Network status | OpenAI and ChatGPT endpoints unreachable from this shell |
| Local provider availability | Ollama 0.31.1 available with `qwen2.5-coder:7b`, `qwen3:8b`, `llama3:8b`, and `llama3.2:3b` |

`codex doctor --json` reported:

```text
auth.credentials: fail - no Codex credentials were found
network.provider_reachability: fail - ChatGPT base URL connect failed
network.websocket_reachability: warning - os error 10013
sandbox.helpers: filesystem sandbox restricted, network sandbox restricted
```

## Direct Pipe Rerun

Command shape:

```powershell
$prompt = 'Reply with exactly: hello from direct pipe'
$stdout = $prompt | codex --ask-for-approval never exec --sandbox read-only --color never --ephemeral - 2>$errFile
```

Observed result:

| Stream | Result |
| --- | --- |
| stdout | Empty |
| stderr | CLI header plus websocket/HTTPS reconnect failures |
| exit code | `1` |

Important stderr excerpts:

```text
approval: never
sandbox: read-only
ERROR: stream disconnected before completion: error sending request for url (https://api.openai.com/v1/responses)
```

Interpretation:

```text
The command reached Codex CLI and accepted stdin, but the OpenAI-backed model call could not complete from this sandbox because network access was forbidden.
```

## CLI Surface Findings

`codex --help` exposed:

```text
exec
review
doctor
sandbox
apply
cloud
exec-server
features
```

`codex exec --help` exposed:

```text
instructions are read from stdin when no prompt is provided or when `-` is used
stdin is appended as a `<stdin>` block when stdin is piped and a prompt is also provided
--json
--output-last-message <FILE>
--output-schema <FILE>
--ephemeral
--ignore-user-config
--ignore-rules
--sandbox <read-only|workspace-write|danger-full-access>
--oss
--local-provider <lmstudio|ollama>
```

Approval policy is a top-level option in this version. Passing `--ask-for-approval` after `exec` returned:

```text
error: unexpected argument '--ask-for-approval' found
```

The working form is:

```powershell
codex --ask-for-approval never exec ...
```

## Local Provider Pipe Test

Because OpenAI network access was blocked, the pipe mechanics were tested with the local Ollama provider:

```powershell
$prompt = 'Reply with exactly: hello from local oss pipe'
$stdout = $prompt | codex --ask-for-approval never exec --oss --local-provider ollama -m qwen2.5-coder:7b --sandbox read-only --color never --ephemeral - 2>$errFile
```

Observed result:

| Stream | Result |
| --- | --- |
| stdout | Final assistant message only |
| stderr | CLI header, prompt transcript, model warning, final message echo, `tokens used` |
| exit code | `0` |

The local model did not obey the exact response instruction in the first local probe:

```text
Hello! I'm ready to assist you. Let me know what I can help with today.
```

Interpretation:

```text
Local-provider mode is useful for testing bridge mechanics, but it is not equivalent evidence for OpenAI-backed Codex quality.
```

## Token Usage Capture

Text mode with local provider printed token usage to stderr:

```text
tokens used
5,930
```

JSONL mode with local provider printed usage to stdout in the final `turn.completed` event:

```json
{"type":"turn.completed","usage":{"input_tokens":5909,"cached_input_tokens":0,"output_tokens":34,"reasoning_output_tokens":0}}
```

OpenAI-provider usage capture could not be tested in this sandbox because the model call failed before completion.

Bridge implication:

```text
Prefer `codex exec --json` for automation. Parse `turn.completed.usage` when present. Treat text-mode `tokens used` on stderr as a fallback only.
```

## JSONL Mode

OpenAI-provider JSONL mode:

```powershell
$prompt | codex --ask-for-approval never exec --sandbox read-only --color never --ephemeral --json -
```

failed due network restrictions, but still emitted machine-readable events to stdout:

```json
{"type":"thread.started","thread_id":"..."}
{"type":"turn.started"}
{"type":"error","message":"Reconnecting..."}
{"type":"turn.failed","error":{"message":"stream disconnected before completion: error sending request for url (https://api.openai.com/v1/responses)"}}
```

Transport diagnostics still appeared on stderr.

Local-provider JSONL mode completed successfully and emitted:

```text
thread.started
item.completed
turn.started
item.completed with type agent_message
turn.completed with usage
```

## Output Last Message

Command shape:

```powershell
$prompt | codex --ask-for-approval never exec --oss --local-provider ollama -m qwen2.5-coder:7b --sandbox read-only --color never --ephemeral --output-last-message $outFile -
```

Observed result:

```text
stdout matched the contents written to --output-last-message
stderr contained token usage
exit code 0
```

Bridge implication:

```text
`--output-last-message` is a stable artifact path for wrappers that do not want to rely only on captured stdout.
```

## File-Backed Prompt Test

Command shape:

```powershell
Get-Content -Raw docs\governance\workers\WP-CODEX-CLI-001.md |
  codex --ask-for-approval never exec --oss --local-provider ollama -m qwen2.5-coder:7b --sandbox read-only --color never --ephemeral 'Read the work package supplied on stdin. Reply with exactly: FILE_PROMPT_RECEIVED'
```

Observed result:

```text
stdout: FILE_PROMPT_RECEIVED
stderr: token usage present
exit code: 0
```

Interpretation:

```text
File-backed prompts work through stdin. When a prompt argument is also present, the file content is appended as stdin context according to the installed CLI help.
```

## ANSI and Control-Character Cleanup

Synthetic test input:

```text
ESC[31mFAIL ESC[0m CRLF backspace PASS bell
```

Cleanup regex tested:

```powershell
$clean = ($text -replace "`e\[[0-9;?]*[ -/]*[@-~]", "") -replace "[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", ""
```

Observed cleaned value:

```text
FAIL
PASS
```

An actual non-terminal run with `--color always` produced zero ANSI escape matches, but the bridge should still strip ANSI/control characters because interactive and local model tools can emit them.

## Encoding Normalization

The discovery session observed:

```text
IΓÇÖm Codex.
```

The characterization reproduced this exact class of mojibake by interpreting UTF-8 bytes as CP437:

```text
Original: I'm ASCII; I’m UTF-8; café; naïve; résumé
CP437 mojibake: I'm ASCII; IΓÇÖm UTF-8; caf├⌐; na├»ve; r├⌐sum├⌐
Recovered: I'm ASCII; I’m UTF-8; café; naïve; résumé
Recovery matched original: true
```

Bridge implication:

```text
The bridge should force UTF-8 where possible and include a targeted recovery path for CP437-decoded UTF-8 mojibake before parsing exact strings.
```

## CODEX_HOME Isolation

Default doctor run used:

```text
C:\Users\CodexSandboxOffline\.codex
```

Override test:

```powershell
$env:CODEX_HOME = "$env:TEMP\codex-home-isolation-empty"
codex doctor --json
```

Observed result:

```text
config.load.CODEX_HOME changed to the override path
auth.credentials.auth file changed to the override path
state.paths.CODEX_HOME changed to the override path
state databases were missing in the new empty home
```

Interpretation:

```text
`CODEX_HOME` structurally isolates config, auth path, logs, and state paths.
```

Unknown:

```text
This run did not prove that multiple authenticated Business seats can run concurrently or that each isolated home can maintain a separate valid ChatGPT auth session. That requires login in each profile outside this restricted shell.
```

## Cloud Command Characterization

`codex cloud --help` exposed:

```text
exec
status
list
apply
diff
```

`codex cloud exec --help` showed:

```text
Usage: codex cloud exec [OPTIONS] --env <ENV_ID> [QUERY]
```

Observed probes:

| Command | Result |
| --- | --- |
| `codex cloud list --json` | Exit `1`; stderr `Not signed in...` |
| `codex cloud list --limit 1` | Exit `1`; stderr `Not signed in...` |
| `codex cloud exec '...'` without `--env` | Exit `2`; stderr required `--env <ENV_ID>` |
| `codex cloud status TASK_ID_PLACEHOLDER` | Exit `1`; stderr `Not signed in...` |
| `codex cloud diff TASK_ID_PLACEHOLDER` | Exit `1`; stderr `Not signed in...` |
| `codex cloud apply TASK_ID_PLACEHOLDER` | Exit `1`; stderr `Not signed in...` |

Unknown:

```text
No real cloud task was submitted. No real task id, status lifecycle, diff payload, or apply behavior was observed.
```

Boundary note:

```text
`codex cloud apply` should remain prohibited for automation until Ingrid approves the local patch boundary and a reviewer can inspect the diff first.
```

## Status Gauge Automation

Prior discovery observed `/status` inside the interactive TUI and recorded account, model, session, directory, context window, and usage-limit information.

This run found no top-level non-interactive `codex status` command and no `exec` option that exposes seat quota or the TUI `/status` gauge. `codex doctor --json` exposes health/auth/network information, but not ChatGPT seat usage limits.

Current finding:

```text
`/status` is proven as an interactive TUI observation only. Non-interactive automation remains unknown.
```

## Recommended Wrapper Behavior

The first bridge wrapper should:

1. Prefer `codex --ask-for-approval never exec --json --sandbox read-only --color never --ephemeral -` for characterization and read-only tasks.
2. Use `workspace-write` only for explicit implementation work packages with an approved write allowlist.
3. Capture stdout, stderr, exit code, command arguments, provider, model, working directory, `CODEX_HOME` label, and timestamps.
4. Parse JSONL stdout when `--json` is enabled.
5. Parse `turn.completed.usage` when available.
6. Treat stderr as operational telemetry, not final content.
7. Normalize UTF-8, strip ANSI/control characters, and retain raw output hashes for audit.
8. Write bridge logs under local runtime storage by default, with deliberate evidence promoted only after classification.
9. Keep cloud commands read-only until cloud task lifecycle and apply behavior are characterized in an authenticated, approved profile.

## Classification of Findings

| Area | Status |
| --- | --- |
| `codex exec` stdin/stdout bridge | Proven in prior authenticated discovery; local-provider transport reproven here |
| OpenAI-backed direct pipe in this shell | Blocked by no credentials and restricted network |
| JSONL event mode | Proven at CLI level |
| Token usage in JSONL | Proven with local provider; OpenAI-provider success path untested here |
| File-backed prompt | Proven with local provider |
| Encoding cleanup | Reproduced and normalized |
| `CODEX_HOME` path isolation | Proven structurally |
| Multi-seat authenticated concurrency | Unknown |
| Cloud task lifecycle | Unknown; current shell unsigned |
| Cloud apply | Unapproved and untested on real task |
| `/status` automation | Unknown; interactive only |
