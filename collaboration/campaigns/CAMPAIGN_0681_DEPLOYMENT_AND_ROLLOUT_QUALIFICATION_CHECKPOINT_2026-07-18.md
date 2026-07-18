# CAMPAIGN-0681 Deployment and Rollout Qualification Checkpoint

Status: **deployed; immediate verification passed; operational rollout incomplete**
Date: `2026-07-18`
Authority: protected acceptance lane, Chief Architect, and Steward
Merge PR: `#423`
Merge commit: `54e267697dc9ff295fdfd45f3ac3f24a97266c8d`
G8 acceptance record commit: `2b74e02620681132bbd6a4cba1da749964f03fe8`

## Integration result

PR #423 was changed from draft to ready and merged into `main` with a merge
commit. GitHub records `merged=true`, `draft=false`, and
`merged_at=2026-07-18T14:18:17Z`. Local `main` and `origin/main` were then
synchronized at `54e267697dc9ff295fdfd45f3ac3f24a97266c8d` with a clean tree.

## Canonical deployment procedure and target

The controlling procedure is
`docs/integration/merge_gated_runtime_host_activation.md`. The target is the
external Windows runtime checkout
`A:\EstateRuntime\host\estate-main\current`, with durable host state under
`A:\EstateRuntime\host\estate-main\state` and Scheduled Task
`Estate Operations Runtime Host`.

Pre-deployment state was captured at `2026-07-18T14:21:21Z`:

- external runtime revision: `e3c215cb78541e1c0f6ac87561bac3efab8c35b5`;
- external runtime was 19 commits behind `origin/main` and clean;
- production-readiness controller tests: 23 passed in 42.34 seconds;
- readiness Python compilation passed;
- local `main` and `origin/main` both resolved to the merge commit;
- the host was stopped and the installed Scheduled Task was in `Ready` state.

Deployment command, run from `A:\theestate`:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
python -m estate.cli.main operations-runtime bootstrap --target estate-main --json
```

The command exited 0 at `2026-07-18T14:24:16Z`. It fetched `origin/main`,
advanced the external clean runtime checkout to
`54e267697dc9ff295fdfd45f3ac3f24a97266c8d`, verified the Scheduled Task,
started PID 3900, and verified a heartbeat. Its machine result records:

- `runtime_matches_remote=true`;
- `scheduled_task_installed=true` and `scheduled_task_verified=true`;
- `host_started=true` and `heartbeat_verified=true`;
- `active_checkout_modifications_performed=false`;
- `provider_execution_performed=false`;
- `dispatch_execution_performed=false`.

## Immediate post-deployment verification

The first completed cycle ran from `2026-07-18T14:24:16Z` through
`2026-07-18T14:24:39Z`; a second completed cycle ran through
`2026-07-18T14:25:32Z`. Both reported `runtime_state=completed`, no runtime
errors, no provider execution, and no dispatch execution. At
`2026-07-18T14:25:38Z` the host was running and sleeping normally between
cycles, PID 3900 was alive, heartbeat age was 7.09 seconds, and no blocking
fault was present.

Verification commands:

```powershell
$env:ESTATE_OPERATIONS_RUNTIME_ROOT = 'A:\EstateRuntime\host\estate-main\current'
$env:ESTATE_OPERATIONS_RUNTIME_HOST_DIR = 'A:\EstateRuntime\host\estate-main\state'
$env:PYTHONPATH = 'A:\EstateRuntime\host\estate-main\current\src'
python -m estate.cli.main operations-runtime host status
python -m estate.cli.main service-health-registry --json
git -C 'A:\EstateRuntime\host\estate-main\current' status --short --branch
git -C 'A:\EstateRuntime\host\estate-main\current' rev-parse HEAD
git -C 'A:\EstateRuntime\host\estate-main\current' rev-parse origin/main
```

The external checkout was clean and both revisions were the merge commit.
Service aggregation reported 10 services: 9 healthy, 0 degraded, 0
unavailable, and 1 unknown because Capability Service remains Draft and
metadata-only. Six non-blocking warnings identify provider `service` values
that do not exactly match catalog service identifiers or names.

## Rollback posture

Rollback was not executed because deployment and immediate health verification
passed. The canonical service rollback controls remain:

```powershell
$env:ESTATE_OPERATIONS_RUNTIME_ROOT = 'A:\EstateRuntime\host\estate-main\current'
$env:ESTATE_OPERATIONS_RUNTIME_HOST_DIR = 'A:\EstateRuntime\host\estate-main\state'
$env:PYTHONPATH = 'A:\EstateRuntime\host\estate-main\current\src'
python -m estate.cli.main operations-runtime host stop
python -m estate.cli.main operations-runtime host status
python -m estate.cli.main operations-runtime host uninstall
```

These controls return the runtime host to a stopped/deactivated state. The
canonical documents do not declare an automated command that restores the
external checkout to its prior code revision; no such rollback capability is
claimed.

## Qualification state

### Live provider: blocked for authority

No matching live execution authorization, Dispatch item, Traffic Controller
authorization, Steward approval record, or expenditure authority was found.
Provider registry presence is not execution authority. No provider was called.
The canonical gate command below may be run only after all required records
exist and match:

```powershell
param(
  [Parameter(Mandatory=$true)][string]$DispatchId,
  [Parameter(Mandatory=$true)][string]$AuthorizationPath
)
Set-Location 'A:\theestate'
$env:PYTHONPATH = (Resolve-Path 'src').Path
python -m estate.cli.main codex-live-execution preview --dispatch-id $DispatchId --authorization $AuthorizationPath --json
if ($LASTEXITCODE -ne 0) { throw 'Live-provider preview failed closed.' }
python -m estate.cli.main codex-live-execution execute --dispatch-id $DispatchId --authorization $AuthorizationPath --confirm-live-execution --json
if ($LASTEXITCODE -ne 0) { throw 'Live-provider execution failed.' }
python -m estate.cli.main codex-live-execution status --dispatch-id $DispatchId --json
python -m estate.cli.main codex-live-execution report --dispatch-id $DispatchId
```

Success, timeout, and provider-refusal/failure handling require separately
authorized bounded Dispatch/authorization records for each intended scenario;
one successful call cannot qualify all three.

### Long-duration availability and freshness: not run

No supervised soak was consumed in this deployment session. The canonical
`estate-main` source policy declares at least two checks over at least 60
seconds, but the persisted target record currently has empty `metadata` and the
manually created WP-0707 case `orc-9e8bcd28fe0c7fba` therefore received the
one-check fallback. That case was not used as qualification evidence. The
persisted/source policy discrepancy must be repaired through the canonical
target configuration path before controller evidence can qualify rollout.

After that repair, the exact controller commands are:

```powershell
Set-Location 'A:\EstateRuntime\host\estate-main\current'
$env:PYTHONPATH = 'A:\EstateRuntime\host\estate-main\current\src'
python -m estate.cli.main operational-targets show --target estate-main --json
python -m estate.cli.main operational-readiness process-one --case-id orc-9e8bcd28fe0c7fba --root 'A:\EstateRuntime\host\estate-main\current' --json
Start-Sleep -Seconds 60
python -m estate.cli.main operational-readiness process-one --case-id orc-9e8bcd28fe0c7fba --root 'A:\EstateRuntime\host\estate-main\current' --json
python -m estate.cli.main operational-readiness show --case-id orc-9e8bcd28fe0c7fba --root 'A:\EstateRuntime\host\estate-main\current' --json
```

This sequence can run unattended once the canonical target record shows the
declared production policy. Any longer required duration must come from an
authoritative specification; none is inferred here.

### Production-like outage, restart, and replay: not run

The external host is an isolated, controllable service surface, but the outage
qualification was not executed in this immediate-verification checkpoint. The
canonical controlled service commands are:

```powershell
Set-Location 'A:\EstateRuntime\host\estate-main\current'
$env:ESTATE_OPERATIONS_RUNTIME_ROOT = 'A:\EstateRuntime\host\estate-main\current'
$env:ESTATE_OPERATIONS_RUNTIME_HOST_DIR = 'A:\EstateRuntime\host\estate-main\state'
$env:PYTHONPATH = 'A:\EstateRuntime\host\estate-main\current\src'
python -m estate.cli.main operations-runtime host status
python -m estate.cli.main operations-runtime host stop
python -m estate.cli.main operations-runtime host status
python -m estate.cli.main operations-runtime host restart
python -m estate.cli.main operations-runtime host status
python -c "from pathlib import Path; import json; from estate.core.runtime_recovery import RuntimeRecoveryManager; print(json.dumps(RuntimeRecoveryManager(Path(r'A:\EstateRuntime\host\estate-main\current')).inspect_startup(), indent=2))"
```

Before this is accepted as qualification, an operator must identify the exact
checkpoint cycle, capture its durable event position and completed side-effect
identifiers before interruption, and compare post-restart replay evidence.
There is no canonical replay CLI; the repository API is
`RuntimeReplayEngine(root).replay_from_checkpoint(cycle_id)`. This controlled
qualification can run without Codex supervision only after an operator supplies
and reviews that real cycle identity and confirms the external host is the safe
test surface.

## Current decision

Deployment is active and immediately healthy. Rollback was not required.
Operational rollout is **not complete**: live-provider qualification is blocked
for missing authority, long-duration qualification is pending and additionally
blocked by the persisted target-policy discrepancy, and production-like
outage/restart/replay qualification is pending. The existing fail-closed
authority-classification false-positive remains deferred calibration work.
