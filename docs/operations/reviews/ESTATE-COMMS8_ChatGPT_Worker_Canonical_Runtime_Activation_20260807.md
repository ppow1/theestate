# Estate Comms8 ChatGPT Worker Canonical Runtime Activation

Date: 2026-08-07

## Result

The worker runtime activation repair is implemented. The mailbox worker now
fails closed unless it is running with the canonical Open WebUI interpreter,
working directory, data directory, governed secret source, required imports,
and consultation store.

## Canonical owner and environment

The accepted Open WebUI owner is `tools/start_openwebui_canonical.ps1`:

- application root / working directory: `A:\AI\OpenWebUI`
- interpreter: `A:\AI\OpenWebUI\.venv\Scripts\python.exe`
- `DATA_DIR`: `A:\AI\OpenWebUI\EstateCanonicalData`
- database: `A:\AI\OpenWebUI\EstateCanonicalData\webui.db`
- secret source: `A:\AI\OpenWebUI\.webui_secret_key`

The worker launch wrapper uses that same interpreter, working directory, and
data directory. The worker preflight accepts either an inherited
`WEBUI_SECRET_KEY` or the existing canonical key file. When the environment
variable is absent, the key is loaded into the worker child process in memory
only; it is not copied to a second file, logged, returned in diagnostics, or
placed on a command line.

The worker is a bounded child launch, not a replacement Open WebUI service.
Its lifetime is independent after launch; it does not require an Open WebUI
restart to obtain the canonical database or secret source.

## Fail-closed checks

`estate.core.chatgpt_worker_runtime.validate_worker_runtime` verifies:

- exact canonical Python interpreter;
- canonical working directory;
- canonical `DATA_DIR` and existing `webui.db`;
- governed secret presence by name/source only;
- `pydantic_core`, `open_webui`, and Estate consultation-store imports;
- consultation-store construction;
- optional ChatGPT CDP reachability.

The CLI exits before queue processing when any required check fails.

## Live acceptance

No request was created during this repair. The pre-existing request
`ec8-41aed424414e43fb` was processed once through the canonical wrapper:

- consultation: `4.00`
- claim dispatch: `claim_next`
- worker: `chatgpt`
- state sequence: `queued` -> `claimed` -> `acknowledged` -> `responded` ->
  `resolved`
- response ID: `resp-4f80d3e88c0048`
- structured classification: `INFORMATION_ONLY`
- execution request: none
- final response: non-empty authoritative reasoning content

The expired/failed earlier worker attempts were not rewritten. No Comms8
mutation beyond the requested processing of the already queued acceptance
request occurred.

The worker state file reported `PROCESSING` during the live operation and the
process exited after authoritative resolution. The consultation store and
Comms8 readback both show the resolved result.

## Verification

Focused runtime, mailbox-worker, Grace, consultation, execution, projection,
and structured-decision tests: `46 passed`.

The canonical command used for live activation was:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\theestate\tools\start_chatgpt_mailbox_worker_canonical.ps1 --once
```

The generic prompt contained no request ID. The authoritative Comms8 event
history records `worker_id=chatgpt`; prose-only completion was not accepted.

## Activation requirements

ACTIVATION REQUIRED:

1. Relaunch the mailbox worker through
   `tools/start_chatgpt_mailbox_worker_canonical.ps1` after deploying worker
   source changes. This loads the canonical venv and inherited/derived
   governed runtime context. Verify the preflight JSON is `ok=true`, then
   verify the worker PID command line uses the canonical Python and the
   authoritative request event history records `worker_id=chatgpt`.
2. Grace Resident Gateway restart is required only for a running Grace owner
   that must load the changed worker-launch/error-handling code. It is not
   required for the standalone canonical worker acceptance above.

The following are NOT REQUIRED by this repair: Open WebUI restart, Comms8
restart, MCP adapter restart, Runtime Host/core restart, dedicated browser
restart, workstation reboot, or ChatGPT reconnect when the existing
authenticated CDP target remains ready.

The following are CONDITIONAL: a fresh ChatGPT conversation/reconnect if the
existing target is unauthenticated or its Live app attachment is stale;
consultation-worker relaunch; execution-router/provider relaunch; and Codex
adapter relaunch when an execution-recommended decision is actually routed.

