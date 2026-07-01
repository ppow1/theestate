# Local Worker Launch Adapter v1

Status: Version 1 Design
Owner: Alfred / Chief of Staff
Classification: Estate Internal

## Purpose

The Local Worker Launch Adapter provides a manual one-shot bridge from the Estate Collaboration Layer to local Ollama workers.

It allows an authorized operator to request a local worker launch through a structured request file instead of manually copying task context between chat, GitHub, and the terminal.

This adapter is not a daemon. It is not autonomous scheduling. It is a manual trigger point that can later be called by Helen, Alfred, or another approved coordinator.

## Operating Model

1. A launch request is written to `collaboration/workers/launch/pending/`.
2. The local operator runs `workers/bootstrap/run_worker_launcher_once.ps1`.
3. The launcher reads one pending request.
4. The launcher validates the requested local model exists in Ollama.
5. The launcher assembles the worker prompt from required institutional documents and the assigned work package.
6. The launcher starts the requested Ollama model.
7. The launcher writes local launch artifacts and a result record.
8. The request is moved to archive or failed.

## Directories

- `collaboration/workers/launch/pending/`
- `collaboration/workers/launch/active/`
- `collaboration/workers/launch/results/`
- `collaboration/workers/launch/archive/`
- `collaboration/workers/launch/failed/`

## Request Fields

A launch request should include:

- `request_id`
- `worker_id`
- `requested_by`
- `model`
- `role`
- `work_package_id`
- `work_package_path`
- `classification`
- `mode`
- `requested_at`
- `notes`

## Runtime Rules

The launcher is subordinate to:

1. Steward direct instruction.
2. Privacy and Boundary rules.
3. Worker Runtime Contract.
4. Instruction Precedence.
5. Assigned work package.

The launcher may perform command-line Git synchronization only when the operator has intentionally invoked it in a context that permits synchronization. Worker prompts must still describe the local runtime accurately.

## v1 Boundaries

Version 1 is intentionally simple:

- Manual one-shot invocation only.
- No background watcher.
- No automatic model selection.
- No autonomous reassignment.
- No credential material in repository files.
- No publication of private local artifacts.

## Future Evolution

Later versions may allow:

- Helen to allocate workers.
- Alfred to route launch requests.
- Discovery to select models by capability.
- Scheduled workers.
- Local transcript capture.
- Worker health reporting.

## Success Criteria

The Estate can place a structured launch request in the Collaboration Layer, run a single local command, and start the requested local worker with the assigned work package and institutional runtime rules loaded.