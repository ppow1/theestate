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

## Governed local-AI comprehension operations slice (2026-08-09)

The same population owner now exposes an operator-invoked `knowledge-index`
local worker. It checks the existing loopback Ollama provider, selects bounded
authorized batches, sends only deterministic packets, parses structured JSON,
applies evidence and scope quality gates, and persists provider/model/source
provenance as candidate interpretations. Results remain reviewable and no
provider can add paths, mutate canonical knowledge, advance an accepted
baseline, or authorize remediation.

The first real run used two troubleshooting batches and produced two
`ACCEPTED_CANDIDATE` results with human review still required. This is a
controlled local-AI worker milestone, not autonomous recurring operation,
Estate-wide comprehension, canonical promotion, resident API exposure, or
remediation authority. Difficulty benchmark expansion and recurring Scheduler
integration remain follow-on work.

## Local-AI quality benchmark and controlled burn-down (2026-08-09)

The governed worker was benchmarked against real admitted schemas, Estate
implementation, diagnostics, and ambiguous PL-0040/PL-0032 material. The
benchmark report is recorded at
`docs/operations/troubleshooting/benchmarks/PL-0040-LOCAL-AI-BENCHMARK-20260809.json`.

Evidence supports `ROUTINE_LOCAL_AI` for the tested Level 1 schema class,
`LOCAL_AI_WITH_REVIEW` for Level 2 and the small Level 3 sample, and
`ESCALATE_TO_STRONGER_REASONING` for Level 4 despite valid candidate output.
Three Level 1 schema candidates were then processed from the real backlog;
all remained candidate-only and human-review-required. Pending canonical
comprehension did not decrease, so coverage was not inflated.

The benchmark also found and repaired two bounded plumbing defects: requested
subtree scans no longer mark unrelated assets missing, and provider-generated
placeholder result IDs are replaced by Estate-owned batch-scoped identities.
Unattended local-AI scheduling, automatic candidate application, canonical
promotion, and remediation remain unauthorized and unwarranted.

## Governed candidate application slice (2026-08-09)

The existing SQLite knowledge-index owner now normalizes candidate fields into
assertions, records deterministic corroboration and evidence strength, stores
review decisions, and applies only low-risk corroborated assertions through a
transactional non-canonical projection. Provider results remain immutable;
provider identities cannot review or apply their own output. Application history
records prior/new values and supports reversal, conflict blocking, source-change
revalidation, and resident-neutral retrieval. Coverage advances only from
applied indexed purpose/owner state; candidate generation and schema-valid
provider output do not advance it. No Level-2, Level-3, or Level-4 candidate is
processed by the Level-1 burn-down, and no recurring scheduler is enabled.

## Deterministic corroboration expansion (2026-08-09)

The knowledge-index owner now stores reusable revision-grounded evidence facts
and assertion-to-fact links. The bounded extractor reads only already-admitted
inventory assets and supports schema metadata/structure, Python imports and
definitions, explicit source/test/documentation references, deterministic
ownership, component mappings, and derived schema tags. Facts preserve source
asset, target, exact value, path/location, source revision/hash, extractor,
certainty, and current/stale state. Provider-derived candidate material is not
accepted as evidence. Corroboration exposes linked facts and keeps unresolved
semantic assertions out of application eligibility.

## Controlled Level-1 production scale acceptance (2026-08-10)

The controlled scale acceptance was started against five admitted engineering
schemas using the existing evidence-enriched worker and single-worker bounded
processing. Five results completed; one subsequent schema work unit timed out
after 180 seconds and was recorded as retryable. The hard-stop condition was
honored, so no configuration, migration, documentation, or registry class was
processed and no scheduler was enabled.

The five completed results produced 17 assertions. Independent evidence
extraction corroborated 14 of them; 11 low-risk purpose, schema-classification,
and deterministic-tag assertions passed non-provider review and were applied
transactionally. Three summary assertions remained non-eligible, and coverage
advanced only for the four assets whose applied understanding completed the
existing purpose/classification rule. SQLite integrity remained valid and the
four pre-existing generated troubleshooting changes remained outside this
campaign. This is a stopped scale-acceptance result, not proof of Estate-wide
or scheduled Level-1 operation; multi-class volume and provider-latency
stability remain open.

## Local provider reliability and evidence-index scale hardening (2026-08-10)

The stopped scale acceptance was resumed only through bounded, single-worker
checkpoints. The exact timed-out schema was retried through the existing work
path and completed with a new batch/result identity, preserving the original
retryable failure. Provider telemetry now records discovery duration, request
start/duration, response bytes, first complete response time, and timeout
phase; a provider failure stops the current bounded invocation.

Evidence extraction now reuses unchanged hash-grounded facts across revision
changes and reports new versus reused facts. An unchanged extraction repeated
with zero new facts after the initial identity transition. Checkpoint A
completed eight additional engineering schemas without invalid results.
Checkpoint B was stopped after two invalid evidence-citation results: one
missing a packet fact ID and one citing a fact outside the packet. No migration,
documentation, or further registry checkpoint was attempted, and scheduling
remains unwarranted. The invalid-result stop is preserved in the associated
Diagnostic Impact Packet.

## Configuration / registry evidence-citation hardening (2026-08-10)

The reliability work was preserved and extended with a packet-local citation
boundary. The evidence-enriched prompt now separates exact packet asset IDs
from the `fact:<sha256>` evidence namespace, requires exact supplied asset IDs,
and tells the provider to remain unresolved when no admitted fact supports a
claim. The result schema checks fact-ID shape, while deterministic Estate
validation checks dynamic packet membership before candidate admission.

Invalid attempts are now preserved in the SQLite v6 `comprehension_attempts`
ledger with raw provider output, packet/prompt versions, packet hash,
validation code, and telemetry. Citation failures use precise fail-closed
categories and stop the bounded invocation. The prior reliability packet
remains historical evidence; this packet supersedes its citation seam without
deleting the failed outputs that are available.

Checkpoint B re-acceptance recovered both original assets. qwen3:8b produced
two further invalid outputs and was stopped: one copied an illustrative asset
placeholder and one invented a near-match fact ID. qwen3-coder produced valid
candidate results for both `data/registry/capabilities.json` and
`data/registry/services.json`; two bounded `data/discovery` controls also had
zero invalid citations. No invalid output was admitted and no new assertion
became application-eligible because the existing deterministic corroboration
and review policy correctly rejected unsupported semantic claims. Scheduling
remains unwarranted; qwen3:8b is not proven for this citation-sensitive class.

## Model-aware local comprehension routing (2026-08-10)

The valid provider/evidence hardening was committed as
`9ea522a943f67e5677957e9142003a87e0652bc2` with the truthful message
`fix: preserve Estate comprehension provider failure evidence`. The four
generated troubleshooting artifacts remain outside that commit.

The existing worker now classifies admitted work and records explainable
model/class route decisions plus fallback lineage in SQLite v7. Registry work
is routed away from qwen3:8b after its two invalid results and to
qwen3-coder:30b-qwencode-20k, which produced valid results on both exact prior
registry assets. Simple configuration controls produced valid results on both
qwen3:8b and qwen3-coder. Explicit comparison runs remain review-required when
qualification evidence is incomplete. Failed attempts and all candidate
interpretations remain preserved; routing does not choose institutional truth
or create applications.

Current bounded evidence supports `REGISTRIES_CONTRACTS = LOCAL_AI_WITH_REVIEW`
with qwen3-coder preferred and qwen3:8b disallowed for the class;
`SIMPLE_CONFIGURATION = LOCAL_AI_WITH_REVIEW` with qwen3:8b preferred for the
small sample; and `JSON_SCHEMA = NOT_YET_PROVEN` for this routing campaign.
No scheduler is enabled or warranted.

## Level-1 qualification matrix checkpoint (2026-08-10)

The recovered matrix resumed from the durable SQLite checkpoint without
replaying the 24 completed schema qualification units or the completed
comparison result. The recovered comparison remained accepted, and no active
work unit was present before resumption.

The two admitted migration assets were processed only through bounded
checkpoints. qwen3-coder returned one citation-invalid result and the route
stopped. qwen3:8b returned one accepted candidate for the real migration JSON
asset, while the second admitted `migrations/estate_knowledge_store/README.md`
unit failed closed because its indexed source revision/content no longer
matched the current repository state. Migration qualification therefore remains
`NOT_YET_PROVEN`; the stale asset must be deterministically revalidated before
further inference.

Five actual admitted documentation assets were processed with
qwen3-coder:30b-qwencode-20k. All five results were valid bounded candidates,
with no invalid citations, unsupported-result failures, timeouts, or new
escalations. Documentation is `LOCAL_AI_WITH_REVIEW` pending a broader sample
and fallback evidence.

The matrix checkpoint now supports:

- `JSON_SCHEMA`: primary qwen3-coder:30b-qwencode-20k; fallback qwen3:8b;
  `LOCAL_AI_WITH_REVIEW`.
- `SIMPLE_CONFIGURATION`: primary qwen3:8b; fallback
  qwen3-coder:30b-qwencode-20k; `LOCAL_AI_WITH_REVIEW`.
- `REGISTRIES_CONTRACTS`: primary qwen3-coder:30b-qwencode-20k; qwen3:8b is
  disallowed for this class; `LOCAL_AI_WITH_REVIEW`.
- `MIGRATIONS`: primary qwen3:8b on the limited valid sample; fallback
  qwen3-coder:30b-qwencode-20k; `NOT_YET_PROVEN`.
- `DOCUMENTATION`: primary qwen3-coder:30b-qwencode-20k; fallback qwen3:8b;
  `LOCAL_AI_WITH_REVIEW`.

After the checkpoint, SQLite integrity remained `ok`; evidence facts grew from
41,354 to 41,462, attempts reached 32, escalations remained 2, applied
assertions remained 44, and application history remained 47. No scheduler,
GPU stress, driver, CUDA, or Windows configuration action was taken.
`SCHEDULED_LEVEL1_NOT_YET_WARRANTED` remains the governing conclusion.
