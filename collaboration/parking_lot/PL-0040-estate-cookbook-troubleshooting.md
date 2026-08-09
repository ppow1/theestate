# PL-0040 — Estate Cookbook Troubleshooting

Status: Foundation Implemented — Estate-wide coverage remains incremental
Priority: High
Category: Estate Operations / Troubleshooting / Diagnostic Engineering
Originator: Pat / Steward
Date Captured: 2026-08-07
Target Milestone: After the current Grace reason -> execute -> observe -> reason vertical slice is operationally proven

## Idea

Create an Estate-wide Cookbook Troubleshooting system that converts known operational workflows into deterministic diagnostic paths instead of requiring each worker or chat to rediscover architecture and failure seams from scratch.

The cookbook should cover the entire Estate, not only Grace, CME, Comms8, ChatGPT, or Codex.

A diagnostic entry should identify known process checkpoints and let an operator determine, in effect:

```text
checkpoint 4.7.7 passed
checkpoint 4.7.8 did not
```

and immediately know the expected input, expected output, authoritative evidence source, likely failure classes, safe recovery action, what not to restart, and the proof required before declaring recovery.

## Troubleshooting Methodology

Study and adapt the disciplined U.S. Navy seven-step troubleshooting tradition or a closely related seven-step Estate method. The Estate version should be evidence-driven and checkpoint-oriented rather than copied mechanically.

The intended methodology should emphasize:

1. recognize and define the symptom;
2. verify the symptom against authoritative evidence;
3. localize the fault to a bounded subsystem or checkpoint boundary;
4. identify probable causes using known inputs, outputs, dependencies, and prior failures;
5. perform the smallest safe corrective action or diagnostic probe;
6. verify restoration through authoritative output and downstream behavior;
7. document the failure, evidence, repair, and new reusable diagnostic knowledge.

The exact Estate formulation should be established when this item is intentionally promoted.

## Desired Cookbook Structure

Future design should investigate reusable entries containing, where appropriate:

- subsystem / workflow name;
- checkpoint identifier;
- expected input;
- expected output;
- authoritative evidence source;
- deterministic probe or diagnostic tool;
- normal timing / lifecycle expectations;
- known failure signatures;
- likely causes;
- safe recovery action;
- prohibited or risky recovery actions;
- smallest activation/restart boundary;
- validation required after repair;
- escalation condition;
- related work packages, incidents, and historical evidence.

The long-term operator experience should support deterministic references such as "run tool 4.7.7" or "inspect checkpoint 4.7.7" rather than broad rediscovery.

## Why It Is Parked

The Estate currently has an active primary acceptance objective: prove Grace ordinary conversation -> higher-level reasoning as warranted -> provider-neutral bounded execution -> Local Execution Adapter / provider -> durable evidence -> automatic reasoning continuation -> Grace final grounded response.

Building the troubleshooting cookbook now would open a broad Estate-wide documentation and diagnostic tooling effort and would distract from that vertical slice.

The concept is therefore preserved now but must not become implementation work merely because it has been captured.

## Promotion Condition

Promote this item when:

1. the current Grace end-to-end operational loop has reached a stable acceptance checkpoint, or a repeated operational failure demonstrates that cookbook work has become the highest-value next slice;
2. enough real failure evidence exists to seed useful checkpoint entries rather than inventing hypothetical diagnostics;
3. the Estate can extend existing Discovery, Audit, operations, and diagnostic tooling rather than creating unnecessary new registries, schedulers, databases, protocols, departments, or architectural layers;
4. the Steward intentionally authorizes the troubleshooting/cookbook effort.

## Explicit Non-Action

Do not begin an Estate-wide diagnostic framework, new registry, new scheduler, new database, new department, or new protocol from this Parking Lot capture.

Do not derail the active Grace/CME acceptance work.

When promoted, first determine which existing Estate subsystems can absorb cookbook indexing, diagnostic execution, evidence capture, and audit integration.

## Related Evidence

- `docs/operations/ESTATE_Grace_Operational_Reasoning_and_Action_Architecture.md`
- `docs/operations/ESTATE_Grace_Reasoning_Loop_Implementation_and_Operations.md`
- The implementation reference explicitly identifies Estate-wide cookbook troubleshooting and diagnostic tooling as deliberate future work.
- Existing detached process-sensitive test harness: `tools/cme_owner_isolation.py`.
- Canonical Parking Lot process: `AI_COMMUNICATION_HINTS.md`.

## 2026-08-08 Promotion Outcome

The Steward promoted and accepted the Living Troubleshooting Foundation. It now
provides deterministic provenance, applicability/staleness detection, a
provider-neutral reconciliation contract, validated change-impact packets,
machine query, locally rendered process diagrams, an auditable accepted-baseline
lifecycle, and active 06:00 Estate-local reconciliation through the existing
Operations Scheduler. This foundation slice is complete; incremental
Estate-wide checkpoint coverage remains ordinary follow-on work rather than a
foundation blocker. Automated universal probes, autonomous Grace cookbook
consultation, and automated remediation remain future work; remediation is not
authorized by this foundation.

The integrated developer-ingestion slice now creates strict impact packets with
Git/worktree provenance, preserves non-promoted candidate knowledge, and exports
a bounded local-AI review delta through the same CLI and reconciliation owner.
An overnight local-AI reviewer remains future work, as do Estate-wide cookbook
population and universal probes.

## Structured knowledge slice (2026-08-09)

The existing PL-0040 lane now includes a provider-neutral operational knowledge
contract for typed incident/troubleshooting records and governed lifecycle
states. Candidate knowledge is separate from canonical checkpoints; promotion
requires evidence and local AI cannot perform it. The Tesla P100/RTX 4090
incident is the first acceptance fixture, including the separate WinError 1224
harness failure and unresolved 0x133 forensics. Estate-wide population,
autonomous consultation, remediation, and the PL-0042 investigation remain
future work.

## Estate comprehension infrastructure slice (2026-08-09)

The existing PL-0040 diagnostics owner now has an authored, normalized
comprehension model for three bounded subsystems: Living Diagnostics, Grace
reasoning-to-execution, and Operations Scheduler reconciliation. The model
records source-grounded components, evidence-qualified relationships,
workflows, stable checkpoints, and deterministic, historical, or candidate
failure seams. The existing Cookbook is linked by reference rather than
duplicated.

The diagnostics CLI can build revision-grounded model views, render
deterministic Mermaid component/workflow diagrams, query bounded model content,
export provider-neutral comprehension packets, and classify source changes as
`REVALIDATION_REQUIRED`. Provider packets remain proposal-only: they cannot
mutate canonical model/Cookbook truth, advance an accepted baseline, or
authorize remediation.

This is a controlled comprehension-infrastructure milestone, not Estate-wide
population, autonomous consultation, universal probe coverage, canonical
promotion, or remediation authority.

## Indexed institutional knowledge infrastructure slice (2026-08-09)

The existing knowledge-index owner now has a migration-governed SQLite runtime
projection for bounded Estate repository inventory and relational retrieval.
It records revision/blob/content provenance, scan progress, deterministic
classification, unknown reasons, ownership and purpose state, many-to-many
tags, component/workflow/checkpoint/failure-seam links, lifecycle assessments,
and revalidation state. The projection is rebuildable and does not replace Git,
governed JSON, evidence, or canonical Cookbook truth.

The existing CLI exposes SQLite initialization, bounded scan/resume, rebuild,
coverage, unknown/stale/lifecycle queries, graph output, and provider-neutral
comprehension packets. This is a bounded indexed-institutional-knowledge
milestone; Estate-wide population, autonomous local-AI consultation, canonical
promotion workflow, resident-facing service exposure, and remediation remain
future work.

## Governed population and resumable worker slice (2026-08-09)

The PL-0040 owner now includes the explicit
`docs/operations/troubleshooting/population-scope.json` admission contract.
Scope is checked before traversal against the governed `ppow1/theestate` Git
worktree. Structural, metadata-only, no-content, and excluded policies are
recorded in SQLite; symlink/root/path escapes fail closed; unknown adjacent
areas are reported without content traversal.

The first deterministic governed inventory completed over 5,827 admitted
assets. The SQLite owner now selects resumable bounded comprehension batches,
builds content-limited provider-neutral packets, validates provider results by
assigned asset identity and source revision, preserves provider provenance and
conflicts, and retains all results as candidate material requiring human or
governed review. Local-AI execution, unattended estate-wide comprehension,
canonical promotion, resident APIs, and remediation remain future milestones.
