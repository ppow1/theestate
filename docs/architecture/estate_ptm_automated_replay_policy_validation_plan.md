# Estate PTM Automated Replay Gate and Policy Validation Plan

Status: Implementation-ready validation planning artifact for TEST-PTM-001A
Package: TEST-PTM-001A — Automated replay gate and policy validation plan
Campaign: PTM-07 — Validation and rollout planning
Launch group: G07A
Integration checkpoint: Gate E — validation and rollout go/no-go
Date: 2026-07-16

## Authority baseline and boundaries

This artifact defines the future automated validation gate for PTM replay, schemas, links, permissions, and execution-topology policy. It is source-backed by the accepted PTM planning baseline, the PTM parallel campaign plan, the PTM dependency manifests, the promoted TEST-PTM-001A Pending package, and the source planning draft.

This plan is not production PTM code. It does not authorize rollout, does not execute migration, does not merge implementation branches, and does not create a second dispatch queue, second task registry, second scheduler, local RTX 4090 worker route, or new governance authority. The future gate must validate the canonical PTM contracts accepted upstream rather than redefining them.

## Required dependency and readiness checks

Before a future formal run of this gate can produce acceptance evidence, the validation runner must confirm these dependency receipts or Chief Architect waivers are present:

| Dependency | Required evidence | Gate use |
| --- | --- | --- |
| `CORE-PTM-003B` | `collaboration/work_packages/completions/CORE-PTM-003B_completion_receipt.md` | Confirms schedule, financial, and KPI projection contracts are frozen enough to replay. |
| `INTAKE-PTM-001B` | `collaboration/work_packages/completions/INTAKE-PTM-001B_completion_receipt.md` | Confirms conversation intake, dedupe, and confirmation paths are governed by canonical intake. |
| `SCHED-PTM-001A` | `collaboration/work_packages/completions/SCHED-PTM-001A_completion_receipt.md` | Confirms schedule dependency and readiness labels are available for dispatch and policy validation. |

A missing, stale, or contradictory dependency receipt must return `blocked`, not `pass` or `fail`, unless a Chief Architect waiver is explicitly attached to the validation report.

## Future validation command contract

The future executable validation suite should expose one aggregate command and deterministic subcommands. The command names below are implementation-ready contract placeholders for the future test surface; they do not create a second scheduler, registry, or queue.

```bash
ptm validate gate-e --replay --schemas --links --permissions --topology --strict
ptm validate replay --ledger <event-log> --projections task,portfolio,schedule,financial,kpi --strict
ptm validate schemas --events --commands --ids --projections --strict
ptm validate links --workspace-routes --resident-commands --dispatch-evidence --migration-sources --strict
ptm validate permissions --authority-boundaries --resident-surfaces --budget-controls --strict
ptm validate topology --no-second-queue --no-second-registry --no-second-scheduler --no-local-worker-route --strict
```

Each command must be independently runnable for diagnosis, but Gate E acceptance must depend on the aggregate command so evidence cannot omit a required policy domain.

## Replay assertions

The replay check must validate all of the following assertions:

1. Replaying the canonical append-only PTM event ledger from an empty projection store yields deterministic task, portfolio, schedule, financial, and KPI projection snapshots.
2. Every event validates against the frozen event envelope, command envelope, identifier contract, hash-chain rules, and projection envelopes accepted by upstream PTM packages.
3. Replay rejects duplicate event IDs, missing event IDs, out-of-order hash-chain links, missing source hashes, missing authority references, and projection writes not derived from accepted events.
4. The replay report records deterministic projection hashes for task, portfolio, schedule, financial, and KPI outputs.
5. Re-running the same ledger with the same accepted contracts produces identical projection hashes and evidence references.

## Schema assertions

The schema check must validate all of the following assertions:

1. Event, command, identifier, projection, intake, schedule, dispatch-evidence, migration, and validation-report payloads conform to their frozen upstream contracts.
2. Unknown fields that could imply budget authority, dispatch authority, local-worker routing, or independent task lifecycle control fail closed unless explicitly allowed by the frozen contract.
3. Optional, estimated, unavailable, stale, and blocked values remain labeled and are not flattened into successful or complete states.
4. Schema version or contract-reference fields point to accepted repository artifacts or recorded external references.

## Link assertions

The link check must validate all of the following assertions:

1. Workspace routes, compact Office card links, Resident command links, dispatch evidence links, migration source mappings, file-import reports, and completion receipts point to canonical PTM records or source-backed evidence.
2. No user-visible route or Resident-visible command points to a private side list, hidden registry, independent scheduler, or alternate dispatch surface.
3. Broken, missing, or ambiguous deep links fail the link check rather than being treated as warnings when they affect task identity, authority, schedule readiness, dispatch evidence, or acceptance evidence.
4. Migration and file-import links preserve source hashes or explicit source references sufficient for audit and rollback.

## Permission and policy assertions

The permission check must validate all of the following assertions:

1. Steward, Chief Architect, Grace/Ops, Traffic Controller, Helen, Codex, Resident-facing surfaces, and any future automation remain within accepted authority boundaries.
2. Resident-visible commands can request, summarize, and route through governed intake but cannot bypass confirmation, create hidden tasks, approve budgets, change dispatch readiness, or self-accept rollout.
3. Grace/Ops operational actions do not imply Steward budget approval or Chief Architect contract acceptance unless an explicit accepted artifact grants that authority.
4. Codex execution remains the mandatory route for this cycle; local RTX 4090 worker routing fails the policy check.
5. Any waiver must identify the waiving authority, affected assertion, bounded scope, expiration or review condition, and evidence reference.

## No-second-path topology assertions

The topology check must validate all of the following assertions:

1. There is exactly one canonical PTM event ledger and task registry for accepted PTM state.
2. Dispatch integration uses the established dispatch queue and evidence chain; it does not create a second dispatch queue or shadow dispatch lifecycle.
3. Schedule readiness labels are projections or governed records; they do not create a second scheduler.
4. Intake, conversation commands, file import, migration, UI routes, and rollout reports all converge on canonical PTM IDs and accepted evidence references.
5. Any detected second queue, second registry, second scheduler, local-worker route, or new governance authority is a blocking failure.

## Required report shape

A future passing or failing run must emit one source-backed report that can be attached to TEST-PTM-001B evidence:

```yaml
ptm_automated_replay_policy_validation_report:
  report_id: string
  generated_at: iso8601
  package_id: TEST-PTM-001A
  campaign_gate: Gate E
  dependency_receipts:
    CORE-PTM-003B: present | waived | blocked
    INTAKE-PTM-001B: present | waived | blocked
    SCHED-PTM-001A: present | waived | blocked
  contract_refs:
    event_contract_ref: string
    id_command_contract_ref: string
    projection_contract_ref: string
    intake_contract_ref: string
    schedule_contract_ref: string
  command_results:
    replay: pass | fail | blocked
    schemas: pass | fail | blocked
    links: pass | fail | blocked
    permissions: pass | fail | blocked
    topology: pass | fail | blocked
  projection_hashes:
    task: string
    portfolio: string
    schedule: string
    financial: string
    kpi: string
  blocking_findings: [string]
  warnings: [string]
  waiver_refs: [string]
  evidence_refs: [string]
  gate_result: pass | fail | blocked
```

The aggregate `gate_result` may be `pass` only when every command result is `pass` and no unwaived blocking finding remains. A `blocked` dependency or missing contract reference must keep the aggregate result `blocked`.

## Promotion evidence notes

- This package remains a validation-planning slice and does not touch production PTM runtime code.
- The plan is bounded to future tests and can be promoted into executable tests after the upstream implementation packages freeze their contracts.
- The command contract deliberately uses a single aggregate gate plus diagnostic subcommands to avoid an incomplete second validation path.
- The topology and policy assertions explicitly guard against second queues, second registries, second schedulers, local-worker routing, and new governance authority.
