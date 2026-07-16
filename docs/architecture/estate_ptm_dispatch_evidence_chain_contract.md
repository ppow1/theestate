# Estate PTM Dispatch Evidence Chain Contract

Status: Implementation-ready planning contract for `DISPATCH-PTM-001`
Authority: Steward / Chief Architect accepted PTM baseline
Scope: Future dispatch integration files only; no production PTM code is authorized by this contract.

## 1. Purpose

The PTM dispatch evidence chain links a canonical PTM task to the already-governed work-package, dispatch, execution, validation, and acceptance artifacts that prove how the task moved through the Estate. The chain is a read-through contract over existing dispatch and work-package surfaces. It must not create a second dispatch queue, second registry, second scheduler, or new governance authority.

## 2. Source-backed authority baseline

- The accepted PTM baseline authorizes promotion and execution preparation for the 28 PTM packages, requires Codex-only routing for this cycle, and explicitly does not authorize production implementation or new authority boundaries.
- The parallel execution plan places `DISPATCH-PTM-001` in launch group `G06A` and Gate D, after schedule readiness gates are stable enough to support migration and dispatch readiness.
- The dependency manifest lists `SCHED-PTM-001A` as the hard dependency for `DISPATCH-PTM-001`; migration package `MIG-PTM-001A` then depends on both `FILE-PTM-001B` and this dispatch evidence contract.
- Existing execution dispatch commands and runtime surfaces are the reuse targets for dispatch queue state, handoff preparation, result reconciliation, attempt recovery, and evidence inspection.

## 3. Evidence chain identity

Every future PTM dispatch evidence chain record must be addressable by a stable `ptm_task_id` and must preserve external references rather than copying mutable source records into a new registry.

Required identity fields:

| Field | Required | Source | Notes |
|---|---:|---|---|
| `ptm_task_id` | Yes | Canonical PTM task projection | Primary lookup key for the evidence chain view. |
| `work_package_id` | Yes when task originates from a work package | Work-package file name or metadata | Examples: `DISPATCH-PTM-001`, `WP-0660`. |
| `work_package_path` | Yes when available | Repository path | Relative path to Pending, completion, or campaign file. |
| `dispatch_id` | Yes after dispatch request exists | Existing execution dispatch queue item | Must point to the existing dispatch item, not a PTM-specific duplicate. |
| `attempt_id` | Conditional | Existing execution attempt runtime | Required when execution-attempt evidence exists. |
| `validation_evidence_path` | Conditional | Completion receipt, test report, or validation report | Must be repository-relative. |
| `acceptance_reference` | Conditional | Chief Architect, Steward, Grace, Helen, or validation gate artifact | Reference only; does not grant acceptance authority. |
| `source_hash` | Conditional | File import or immutable source mapping | Required when migration/import source proof exists. |

## 4. Chain states

The dispatch evidence chain is a derived view over canonical PTM and existing dispatch state. Future implementation may expose these normalized states, but state transitions remain owned by the existing sources of truth.

| Normalized state | Minimum evidence | Dispatch authority boundary |
|---|---|---|
| `not_dispatch_ready` | PTM task exists but lacks required schedule readiness or dependency evidence | No dispatch request may be inferred. |
| `ready_for_dispatch_review` | Schedule readiness gate satisfied and work-package/campaign references are present | Review only; Traffic Controller/authorized lane decides movement. |
| `dispatch_requested` | Existing dispatch queue item exists and references the PTM task or work package | Existing dispatch queue remains authoritative. |
| `handoff_prepared` | Existing handoff artifact exists for the dispatch item | Handoff preparation is not live provider execution. |
| `execution_attempted` | Existing execution attempt evidence exists | Attempt runtime remains authoritative for cancellation/recovery. |
| `result_reconciled` | Existing result reconciliation artifact exists | Reconciliation does not imply acceptance. |
| `validation_recorded` | Validation report or completion receipt exists | Validation gate remains authoritative. |
| `accepted` | Acceptance reference exists from the proper review lane | Acceptance authority remains with the named human/governance lane. |
| `blocked_or_cancelled` | Existing dispatch item, attempt, or package evidence shows blocked/cancelled state | Existing dispatch/review records remain authoritative. |

## 5. Link contract

Future PTM dispatch integration must implement links as references with provenance metadata. A link is valid only when it satisfies all of the following:

1. `source_system` identifies the existing source surface, such as `ptm_task_projection`, `work_package_file`, `execution_dispatch`, `execution_attempt`, `execution_result_reconciliation`, `completion_receipt`, or `acceptance_record`.
2. `source_reference` stores a stable repository path, dispatch ID, attempt ID, or acceptance reference.
3. `relationship` is one of `originates_from`, `implements`, `requested_dispatch`, `prepared_handoff`, `attempted_execution`, `reconciled_result`, `validated_by`, `accepted_by`, `blocked_by`, or `superseded_by`.
4. `observed_at` records when the link was observed or projected.
5. `integrity` records `unverified`, `path_exists`, `hash_verified`, or `authority_verified` without overstating proof.
6. `notes` may describe ambiguity, but must not encode hidden scheduling, dispatch, or acceptance decisions.

## 6. Validation rules for future implementation

A future implementation of this contract must pass documentation or unit validation proving:

- a PTM task can be traced to its work-package path and completion receipt when those artifacts exist;
- a PTM task can reference an existing dispatch item without creating a new queue entry;
- a dispatch item can be traced through handoff, execution attempt, reconciliation, validation, and acceptance references when those artifacts exist;
- missing optional evidence is reported as `unavailable` or `not_yet_recorded`, not as failure or acceptance;
- blocked, cancelled, duplicate, or superseded evidence remains visible and is not silently flattened into success;
- Codex-only routing is preserved for the accepted PTM implementation cycle unless Chief Architect acceptance changes the routing baseline.

## 7. Stop/replan triggers

Stop and open a replan note before implementation if any future package requires:

- a new dispatch queue, registry, scheduler, or governance authority;
- mutation of frozen event, ID, projection, intake, route, schedule, or validation contracts;
- local RTX 4090 routing during the accepted Codex-only cycle;
- acceptance decisions inferred from validation evidence without the required human/governance lane;
- active execution estimates above 60 minutes without evidence-based decomposition.
