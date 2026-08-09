# PL-0040 — Estate Cookbook Troubleshooting

Status: Incremental foundation implemented; Estate-wide population remains parked
Priority: High
Category: Estate Operations / Troubleshooting / Diagnostic Engineering
Originator: Pat / Steward
Date Captured: 2026-08-07
Target Milestone: After the current Grace reason -> execute -> observe -> reason vertical slice is operationally proven

## Idea

Create an Estate-wide Cookbook Troubleshooting system that converts known operational workflows into deterministic diagnostic paths instead of requiring each worker or chat to rediscover architecture and failure seams from scratch.

The cookbook should cover the entire Estate, not only Grace, CME, Comms8, ChatGPT, or Codex.

A diagnostic entry should identify known process checkpoints and let an operator determine, in effect, that one checkpoint passed and the next did not, then immediately know the expected input, expected output, authoritative evidence source, likely failure classes, safe recovery action, what not to restart, and the proof required before declaring recovery.

## Troubleshooting Methodology

Study and adapt the disciplined U.S. Navy seven-step troubleshooting tradition or a closely related seven-step Estate method. The Estate version should be evidence-driven and checkpoint-oriented rather than copied mechanically.

The intended methodology should emphasize symptom definition, authoritative verification, fault localization, probable-cause analysis, the smallest safe corrective action or probe, verification of restoration, and capture of reusable diagnostic knowledge.

## Desired Cookbook Structure

Future design should investigate reusable entries containing checkpoint identifiers, expected inputs and outputs, authoritative evidence sources, deterministic probes, timing/lifecycle expectations, known failure signatures, likely causes, safe recovery actions, prohibited recovery actions, smallest restart boundaries, validation requirements, escalation conditions, and related historical evidence.

The long-term operator experience should support deterministic references such as `run tool 4.7.7` or `inspect checkpoint 4.7.7` rather than broad rediscovery.

## Why It Is Parked

The Estate currently has an active primary acceptance objective around the Grace end-to-end reasoning and execution loop. Building the cookbook now would open a broad Estate-wide documentation and diagnostic tooling effort and distract from that vertical slice.

The concept is preserved now but must not become implementation work merely because it has been captured.

## Promotion Condition

Promote when the current Grace loop is stable or repeated operational failures make cookbook work the highest-value next slice; enough real failure evidence exists to seed useful entries; existing Discovery, Audit, operations, and diagnostic tooling can be reused; and the Steward intentionally authorizes the effort.

## Explicit Non-Action

Do not begin a new Estate-wide registry, scheduler, database, department, or protocol from this capture. Do not derail active Grace/CME acceptance work. When promoted, first determine which existing Estate subsystems can absorb cookbook indexing, diagnostic execution, evidence capture, and audit integration.

## Related Evidence

- `docs/operations/ESTATE_Grace_Operational_Reasoning_and_Action_Architecture.md`
- `docs/operations/ESTATE_Grace_Reasoning_Loop_Implementation_and_Operations.md`
- `tools/cme_owner_isolation.py`
- `AI_COMMUNICATION_HINTS.md`

## Implemented foundation (2026-08-08)

Deterministic implementation provenance, accepted-baseline reconciliation, the
Diagnostic Impact Packet schema, provider-neutral developer packet creation,
fail-closed ingestion, affected-checkpoint discovery, candidate preservation and
query, and the bounded local-AI delta contract are implemented. Existing 06:00
Operations Scheduler integration remains the scheduled reconciliation owner.

Still incremental/future: Estate-wide checkpoint population, an autonomous
overnight local-AI reviewer, universal deterministic probes, autonomous Grace
cookbook consultation, and automatic remediation. This update does not close
PL-0040 or authorize those capabilities.

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

The existing PL-0040 diagnostics owner now provides a normalized,
revision-grounded comprehension model for Living Diagnostics, Grace
reasoning-to-execution, and Operations Scheduler reconciliation. It preserves
evidence-qualified relationships, workflows, checkpoints, failure seams,
Cookbook references, deterministic Mermaid views, bounded provider-neutral
packets, and source-change revalidation state.

The packet boundary remains proposal-only and cannot mutate canonical truth,
advance an accepted baseline, promote knowledge, or authorize remediation.
This milestone proves bounded comprehension infrastructure only; it does not
perform Estate-wide population or close PL-0040.

## Indexed institutional knowledge infrastructure slice (2026-08-09)

The existing PL-0040 owner now includes a migration-governed SQLite projection
for bounded deterministic repository inventory, scan/resume state, provenance,
ownership/purpose/tag classification, relational component/workflow/checkpoint
and failure-seam links, coverage, lifecycle assessment, staleness, graph views,
and bounded provider-neutral packets. The database is runtime-generated and
rebuildable; Git and governed artifacts remain authoritative.

This milestone supports controlled indexed population but does not perform
Estate-wide population, autonomous provider review, canonical promotion,
resident API exposure, or remediation. PL-0040 remains open for those later
milestones.

## Governed population and resumable worker slice (2026-08-09)

The existing lane now has a versioned repository population scope and a
deterministic pre-traversal enforcement boundary. The first admitted inventory
completed over 5,827 assets while excluding generated/runtime/evidence/Git
internals and limiting data/archive/resident material to metadata or no-content
policies.

SQLite migration 2 adds scope boundaries, resumable comprehension batches,
provider-result provenance, and candidate interpretation history. Work packets
are selected by the Estate, contain only assigned structural assets, and cannot
be expanded by a provider. Result ingestion is fail-closed, idempotent for
identical output, conflict-preserving, and permanently candidate-only pending
governed review. This does not authorize unattended local-AI population,
canonical promotion, resident service exposure, or remediation.

## Governed local-AI comprehension operations (2026-08-09)

The existing owner now provides a bounded `knowledge-index work-run`
operation over the already-admitted queue. It reuses the loopback Ollama
provider, performs a live health/model check, sends only Estate-built packets,
requires structured candidate JSON, validates evidence and assigned identity,
and records model/source provenance and quality outcome. The first real run
completed two troubleshooting work units as accepted candidates requiring
human review. Local AI remains a provider, not an authority: scope expansion,
canonical promotion, baseline advancement, remediation, and unattended
recurring scheduling remain prohibited.
