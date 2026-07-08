# Codex CLI Capability Matrix

Status: Draft Characterization
Owner: Chief Architect
Boundary Authority: Ingrid / Privacy and Boundary Office
Classification: Estate Internal
Created: 2026-07-07

## Scope

This matrix summarizes what Codex CLI can and cannot currently do for Estate use, based on:

- the 2026-07-07 authenticated discovery session
- the 2026-07-07 characterization rerun in this sandbox
- installed CLI help for `codex-cli 0.142.5`
- local-provider tests through Ollama

## Capability Matrix

| Capability | Current finding | Evidence | Classification |
| --- | --- | --- | --- |
| Non-interactive stdin prompt | Supported | Prior OpenAI discovery succeeded; local-provider rerun succeeded | Immediate safe use with bounded prompts |
| Capturable stdout final answer | Supported | Prior discovery captured exact OpenAI output; local-provider text mode returned final answer on stdout | Immediate safe use |
| Stderr telemetry | Supported but noisy | Headers, warnings, transcripts, token usage, and errors appear on stderr | Immediate safe use if parsed carefully |
| JSONL event output | Supported | `codex exec --json` emitted JSONL on stdout | Recommended bridge mode |
| Usage capture | Partially supported | Local-provider JSONL emitted `turn.completed.usage`; text mode emitted `tokens used` on stderr | Experimental until OpenAI success path is verified |
| `--output-last-message` | Supported | Local-provider run wrote the same final answer as stdout | Immediate safe use |
| File-backed prompts | Supported | Existing work package piped through stdin returned expected local-provider response | Immediate safe use |
| Prompt argument plus stdin | Supported | Help states stdin is appended as a `<stdin>` block | Immediate safe use |
| Read-only sandbox | Supported | Help exposes `--sandbox read-only`; reruns used it | Immediate safe default |
| Workspace-write sandbox | Supported by CLI | Help exposes `--sandbox workspace-write` | Experimental, requires explicit work package and allowlist |
| Danger full access | Supported by CLI | Help exposes `danger-full-access` and bypass flags | Prohibited for bridge automation |
| Top-level approval policy | Supported | `codex --ask-for-approval never exec ...` works; after `exec` it fails | Immediate safe use when correctly placed |
| OpenAI-backed direct pipe in current shell | Blocked | No credentials and network denied with os error 10013 | Blocked in this environment |
| Local OSS provider through Codex CLI | Supported | `--oss --local-provider ollama` completed with Ollama | Experimental transport/mechanics use |
| Exact-output reliability with local model | Mixed | Local qwen2.5-coder failed one exact-output prompt, passed file-backed prompt | Not a substitute for OpenAI Codex quality |
| ANSI/control cleanup | Required | Synthetic cleanup test passed; actual non-terminal run had zero ANSI escapes | Immediate implementation requirement |
| UTF-8 normalization | Required | CP437 mojibake reproduction matched discovery (`IΓÇÖm`) and recovered | Immediate implementation requirement |
| `CODEX_HOME` profile paths | Structurally isolated | `codex doctor --json` used override paths for auth/config/state | Experimental for multi-seat use |
| Authenticated multi-seat profiles | Unknown | No authenticated profile available in current shell | Unapproved until tested |
| Interactive `/status` fuel gauge | Available interactively | Prior discovery observed account/model/quota/context data | Manual observation only |
| Non-interactive seat status | Unknown | No `codex status` command found; doctor does not expose quota | Unknown |
| Cloud list/status/diff/apply surface | Present | Help exposes commands | Experimental read-only after sign-in |
| Cloud task submission | Present but untested | Requires `--env <ENV_ID>`; no environment available here | Unapproved until environment classified |
| Cloud apply | Present but untested on real task | Placeholder command stopped at sign-in check | Prohibited for automation |
| Output schema | Present | `--output-schema <FILE>` appears in help | Untested |

## Immediate Safe Use

The Estate can use Codex CLI immediately for:

- bounded characterization
- deterministic small prompts
- local-provider bridge mechanics tests
- documentation-only tasks with explicit allowed paths
- JSONL capture and parser development
- work-package prompt construction tests

Safe default command shape:

```powershell
$prompt | codex --ask-for-approval never exec --sandbox read-only --color never --ephemeral --json -
```

## Experimental Use

The following are useful but need more controlled testing:

- OpenAI-backed `codex exec --json` success-path usage parsing
- `workspace-write` implementation packages with write allowlists
- `--output-schema` structured result enforcement
- separate authenticated `CODEX_HOME` profiles for multiple seats
- non-interactive fuel-gauge capture
- cloud `list`, `status`, and `diff` in a signed-in profile
- Codex Cloud task submission in a classified cloud environment

## Prohibited Or Unapproved Use

The following should not be automated yet:

- unrestricted access to all of `A:\theestate`
- `--sandbox danger-full-access`
- `--dangerously-bypass-approvals-and-sandbox`
- prompt export of credentials, `.env`, auth files, resident-private content, or local runtime state
- automatic `codex cloud apply`
- automatic local patch application from cloud diffs
- multi-seat rotation without profile inventory and audit labels
- silent background loops that consume ChatGPT seat quota without a visible budget policy

## Recommended Minimal Production Bridge

Version 1 should be a local wrapper, not a broad orchestrator.

It should:

1. Read a work package or prompt file.
2. Validate the request against the boundary policy.
3. Build a deterministic prompt.
4. Invoke `codex exec` with explicit provider, model, sandbox, approval policy, and working directory.
5. Prefer `--json`.
6. Capture stdout, stderr, exit code, and duration.
7. Normalize encoding and strip terminal noise.
8. Parse final result and usage.
9. Record a local audit log under `runtime/`.
10. Write only approved artifacts.
11. Require human review before promotion or merge.

## Unknowns To Resolve Before Routine Production Use

- Can `/status` be automated without TUI scraping?
- Does OpenAI-backed JSONL success output match the local-provider `turn.completed.usage` shape?
- Can each `CODEX_HOME` hold a separate authenticated ChatGPT Business account?
- Can multiple `CODEX_HOME` profiles run concurrently without state collisions?
- What are Codex Cloud task ids, lifecycle states, and diff payloads?
- Can cloud diff be inspected safely without any local mutation?
- What exact prompt classifications should Ingrid approve for external model calls?
