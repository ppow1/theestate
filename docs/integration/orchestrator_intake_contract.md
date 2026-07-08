# Orchestrator Intake Contract

Status: Implemented  
Classification: Estate Internal

## Purpose

The Orchestrator intake contract is the Estate front door for governed work requests before scheduling begins. It preserves request provenance, classification, provider expectations, validation needs, allowed and forbidden paths, and Steward-visible blocked states without implementing a scheduler or provider runner.

## Intake Model

An intake request is a JSON object with required identity, provenance, classification, mission, and summary fields. Optional fields describe work package references, assignment references, requested worker/provider details, capabilities, path boundaries, expected outputs, budget source, and metadata.

Allowed classifications are `Public`, `Estate Internal`, `Restricted`, `Steward Only`, and `Local Only`. Allowed priorities are `low`, `normal`, `high`, and `urgent`. Allowed initial states are `pending`, `accepted`, `blocked`, and `rejected`. New `source` strings are preserved rather than rejected so future planning providers, offices, or adapters can integrate without contract redesign.

## Status Model

Each submitted request produces an intake status containing the request identity, current state, timestamps, provenance, work package/provider references, classification, priority, mission, summary, validation and approval flags, blocked reason, artifact paths, and metadata.

Sensitive summaries are redacted in CLI output unless `metadata.summary_safe` is `true`.

## Runtime Artifact Locations

The runtime writer creates these directories and files as needed:

- `runtime/orchestrator/intake/pending/`
- `runtime/orchestrator/intake/accepted/`
- `runtime/orchestrator/intake/blocked/`
- `runtime/orchestrator/intake/status/latest.json`
- `runtime/orchestrator/intake/status/queue.json`
- `runtime/orchestrator/intake/events/`

Runtime directories are generated at execution time and are not committed as empty placeholders.

## Validation and Block Behavior

Invalid requests fail and exit non-zero through the CLI when required fields are absent, the classification is unknown, the priority is unknown, the timestamp is invalid, or the initial state is invalid.

Governed requests can be valid but blocked. The runtime writes blocked artifacts and exposes the blocked reason when:

- `Restricted` requests omit `boundary_review_required: true`.
- `Steward Only` requests omit explicit approval metadata (`approval` or `steward_approval`).
- execution-oriented requests omit `requested_provider_type`.
- `source` is `work_package` and `work_package_path` is absent.

Blocked intake is a visible governed outcome and the submit command exits zero while printing `BLOCKED`.

## CLI Examples

```powershell
Clear-Host
cd A:\theestate
.\estate.bat orchestrator-intake-submit --request .\runtime\examples\intake.json
.\estate.bat orchestrator-intake-list
```

The Python module entry point is also available in tests and local automation:

```powershell
Clear-Host
cd A:\theestate
python -m estate.cli.main orchestrator-intake-submit --request .\runtime\examples\intake.json
python -m estate.cli.main orchestrator-intake-list --json
```

## Relationship to Planning Providers

Planning providers can submit requests with `source: "planning_provider"`, a `source_artifact`, and work package references. The intake contract does not run the provider and does not treat planning output as authorization to execute; it records the handoff for future Orchestrator scheduling.

## Relationship to Execution Providers

Execution providers are referenced through `requested_provider_type`, `requested_provider_id`, `requested_worker_id`, required capabilities, expected outputs, and path boundaries. Intake does not select, start, or monitor an execution provider.

## Relationship to Operational Event Feed

Each intake submission creates an intake-local JSONL event artifact and attempts to record a compatible shared operational event. Accepted pending intake emits `Job Accepted`; Restricted blocked intake emits `Boundary Review Required`; Steward approval blocks emit `Waiting for Approval`; other blocked provider/work-package cases emit `Worker Blocked`.

## Future Orchestrator Notes

Future Orchestrator packages can consume `queue.json`, individual pending/blocked request artifacts, and latest status without redesign. Scheduling, provider registration, provider execution, Office decision controls, and validation orchestration remain separate follow-on responsibilities.
