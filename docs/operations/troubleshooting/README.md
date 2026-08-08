# Estate Living Troubleshooting Foundation

## Start here when something is broken

Open `generated/index.html`, or run `python tools/estate_diagnostics.py search
"symptom"`. Identify the workflow, last proven checkpoint, next unproven
checkpoint, and its authority. Run the narrow probe, repair only that boundary,
verify downstream recovery, and preserve evidence.

`cookbook.json` is the canonical authored knowledge. The implementation
manifest, search index, freshness report, and HTML below `generated/` are
derived; never edit them. No service, database, model, or external provider is
required.

## Provenance contract

The model deliberately separates artifact identity (canonical path), artifact
revision (SHA-256 and Git blob), repository revision (commit), component
identity, meaningful declared component version, interface/schema version,
Estate Change/work-package lineage, document/checkpoint revision,
validated-against evidence, and installation context (branch, worktree, dirty
state). A timestamp is never a semantic version. There is no Estate-wide
embedded-version doctrine; therefore every governed artifact is identified by
path + immutable content hash + Git identity/context, while semantic versions
remain `NOT_DECLARED` unless they carry compatibility meaning.

Tracked modified files retain their HEAD blob identity but expose the current
working-content hash and `MODIFIED`. Material untracked governed files expose
`LOCAL_REVISION` and `UNTRACKED`. Repository and running installation provenance
remain distinct; the Estate currently has no universal deployment provenance,
so installed state must not be inferred from this repository snapshot.

## Checkpoints and applicability

IDs are immutable `DOMAIN.WORKFLOW.CHECKPOINT` numeric triples (for example
`4.1.1`). Published IDs are never renumbered; aliases support renamed concepts,
deprecated IDs remain resolvable, and sub-checkpoints allocate the next stable
number. Applicability (`VALIDATED`, `REVALIDATION_REQUIRED`, `UNKNOWN`,
`PROPOSED`) is separate from maturity (`DOCUMENTED`, `OBSERVED`, `PROVEN`,
`AUTOMATED`). Missing or changed dependencies conservatively require
revalidation. A checkpoint supports purpose, links, input/output, authority,
probe, failures, causes, recovery, prohibited actions, restart boundary,
verification, escalation, dependencies, applicability, incidents, maturity,
and validation provenance.

The seven steps are: define the symptom; verify it; localize the boundary;
identify probable causes; perform the smallest safe probe/correction; verify
restoration; preserve knowledge. Keep symptom, observation, finding,
hypothesis, proven root cause, corrective action, and recovery evidence distinct.

Authority follows owning durable state: consultation store for eligibility;
Comms8 records/events for lifecycle; request/attempt/evidence for execution;
durable owner/lease plus process existence for CME; actual turn metadata plus
Model Control and runtime state for models. Browser interaction is evidence,
not transport authority; GitHub is a projection, not runtime authority.

## Provider-neutral reconciliation

Stage 1 is deterministic: enumerate/hash, inspect Git, compare dependencies,
ingest candidate Diagnostic Impact Packets, mark staleness, build indexes/HTML,
validate structure, and persist a freshness report. It completes safely with no
AI provider. Stage 2 is optional reasoned maintenance requested as a capability
through existing provider/model-control routing. Candidate guidance never
becomes `VALIDATED` without revalidation; unavailable reasoning leaves durable
pending review and never preserves false certainty. Knowledge provenance uses
`DETERMINISTIC`, `LOCAL_AI`, `EXTERNAL_AI`, `HUMAN`, or `MIXED`; provider detail
is audit metadata, not architecture.

The canonical Operations Scheduler is the scheduling owner. Register the
read-only command in `operations/operations_scheduler/living_diagnostics_job.json`
for nominal 06:00 Estate-local execution; this package creates no scheduler.
Accepted change/work-package completion may emit a packet conforming to
`schemas/troubleshooting/diagnostic_impact_packet_v1.schema.json` and trigger
incremental reconciliation. The full daily sweep independently detects packets
that were omitted and emits `CHANGE_WITHOUT_DIAGNOSTIC_IMPACT_METADATA`.

## Commands and machine contract

```text
python tools/build_estate_diagnostics.py
python tools/validate_estate_diagnostics.py
python tools/estate_diagnostics.py version-status --json
python tools/estate_diagnostics.py freshness --json
python tools/estate_diagnostics.py search "queued but never claimed"
python tools/estate_diagnostics.py failure COMPOSER_NOT_READY
python tools/estate_diagnostics.py checkpoint 3.1.1 --json
python tools/estate_diagnostics.py affected-by src/estate/core/continuous_momentum_engine.py
python tools/estate_diagnostics.py reconcile --accepted-manifest PATH
python tools/estate_diagnostics.py reconcile --incremental --impact-packet PACKET
```

Future Grace/operations consumption reads `freshness-report.json` and surfaces
only material exceptions. Probe producers should return CHECKPOINT, RESULT,
EXPECTED, OBSERVED, AUTHORITY, SOURCE, FAILURE_CLASSIFICATION, NEXT_CHECKPOINT,
TIMESTAMP, and VERSION_CONTEXT. This is not autonomous remediation.

The detached-process checkpoint preserves the documented requirement to use
the isolation harness where installed: launch outside the observing worker,
capture evidence directory/stdout/stderr/exit/completion marker, and never run a
process-sensitive CME ownership proof directly under an observer that can kill
its child. The harness is referenced operationally but is not present in this
repository revision; the current repository source explains the boundary.

## Historical replay set

Seeded evidence maps stale owner/active lease, composer not ready, request
processing limitation, MCP not invoked, claim-next schema not used,
context required, malformed execution/evidence requests, evidence exhaustion,
Steward escalation, provider quota/capacity, observer effect, bootstrap fallback,
and dirty worktree ambiguity. Replay queries select the authority and smallest
safe action; they do not reconstruct unsupported incident detail.
