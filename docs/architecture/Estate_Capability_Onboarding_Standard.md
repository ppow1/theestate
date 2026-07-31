# Estate Capability Onboarding Standard v1

Status: Estate-wide implementation standard
Classification: Estate Internal

## Purpose

This is the single onboarding contract for a new capability, provider, adapter,
resident-owned wrapper, service, connector, human worker, or bounded tool. It
is executor-neutral: Grace, Helen, a local coding model, a qualified
Engineering worker, or a human engineer can follow the written package alone.

The design has three layers:

1. Estate Core Capability Contract: identity, ownership, I/O, authority,
   evidence, lifecycle, schema, receipt, replay, and acceptance.
2. Resident Overlay: owner, safety and reasoning boundaries, source rules,
   escalation, and acceptance rules.
3. Provider/Tool Overlay: model, binary, service, endpoint, workflow, connector,
   or human-worker implementation details.

The existing provider catalog at config/providers/catalog.json remains the
canonical provider registry. data/registry/capabilities.json remains the
capability source surface. The Estate capability registry is a read-only
aggregation, not a replacement. A small closed resident-facing declaration
contract is defined at schemas/residents/resident_capability_manifest_v1.schema.json.

## Definitions and boundaries

A capability definition records a stable need, owner, taxonomy, inputs, outputs,
classification, boundaries, and maturity. A provider declaration is only a
catalog statement. An adapter implementation is only a technical implementation.
Resident authorization is owner permission. Dispatch authorization is the
complete fresh authority chain for one bounded attempt. A successful execution
is evidence for that attempt, not new authority. Operational status is current
availability evidence. Institutional acceptance is a separate explicit record.

Every package supplies a stable capability ID and version, resident/department
owner, requested maturity, current limitations, provider/tool bindings, exact
input/output contract, evidence sources, and source-of-truth references. The
record states read-only/write-capable/execution-capable, networked/local-only,
model/service/connector/human-backed status and the highest allowed data
classification.

Exact allowed inputs, repository-relative reads, writes, and expected outputs
are required. An explicit not_applicable rationale is required for a
non-execution or read-only tool. Wildcards, broad directories, arbitrary caller
paths, implicit authority, and provider-added paths are prohibited.

Prompt, request, source, or evidence provenance names the canonical record,
source type, immutable-byte digest where applicable, originator, timestamp,
freshness, and transformations. Legal and historical tools preserve citations
and uncertainty; transcription preserves media identity; image generation
preserves workflow and model provenance.

Technical execution uses the existing Grace -> Helen -> PTM -> Engineering ->
Operations -> Dispatch -> final handoff -> registered adapter lifecycle. A
non-execution tool documents its owner authorization and receipt instead of
creating a second queue or readiness system.

## Evidence, records, and failure

Helen reports qualification, availability, capacity, authorization, and
provider health separately, with source, observation time, scope, expiry, and
subject identity. A catalog entry is not qualification; health is not authority.
PTM readiness is required for dependency-changing or Engineering execution work,
not merely for describing a read-only capability.

New authority records use closed versioned Draft 2020-12 schemas and canonical
repository-root-bounded create-once persistence. Complete writes, flush,
fsync/close, parent-directory durability where supported, equivalent replay,
and conflicting-replay failure are required. Artifacts and receipts carry
identity, scope, source/input digest, provider/tool identity, runtime identity,
authority references, validation evidence, and reconciliation. Full prompts and
secrets do not belong in receipts.

Missing authority, schema, scope, evidence, health, freshness, or registration
fails closed before publication. Timeout, cancellation, collision, partial
output, and provider failure produce truthful evidence and cannot look like
success. Equivalent replay is deterministic; conflicting replay fails without
widening scope or invoking a second execution.

## Maturity model

| Level | Required evidence | Prohibited behavior | Transition authority |
|---|---|---|---|
| 0 Concept | Need and owner identified. | No registration or dispatch. | Owner records need. |
| 1 Registered | Stable ID, owner, I/O, classification, boundaries. | Not live-dispatchable. | Owner; Steward/Architect for reserved boundaries. |
| 2 Provider Available | Candidate provider/tool and evidence sources. | No execution. | Owner plus Helen candidate evidence. |
| 3 Governed | Adapter/wrapper, closed schemas, authority, receipts, replay, failures, tests. | No use outside declared scope. | Engineering/owner; PTM and Dispatch where required. |
| 4 Operational | Fresh governed live acceptance, synchronized runtime, runbook, exact scope, discovery. | No inferred acceptance or scope expansion. | Owning department and Steward review. |
| 5 Institutionally Accepted | Explicit acceptance record for named scope. | No inference from operational success. | Institutionally authorized decision-maker. |

Evidence expiry or regression may make a Level 4 capability unavailable or
not_dispatchable without rewriting historical maturity evidence. Helen reports
maturity and current availability separately. Grace tells the requester whether
the capability exists, its maturity, current availability/dispatchability,
required authorization, and whether an enabling project blocks resumption.

## Registration, testing, and transition

Registration updates the existing provider catalog, capability source, resident
manifest, service manifest, or adapter registry only as required. It must not
change an existing provider's scope silently. Installed runtimes, services,
models, and package versions are synchronized before Level 4 declaration.
Removal/deprecation creates a supersession record, safely drains queued work,
preserves historical receipts, and removes only after active references are
checked.

Packages include unit, schema, integration, negative/fail-closed, replay,
collision, cancellation, and boundary tests. Level 4 requires one fresh
governed live acceptance unless a lower-level/non-execution exemption is
explicitly recorded. Successful execution never grants institutional
acceptance.

## Grace, Helen, and stop conditions

Grace consumes existence, maturity, current availability, dispatchability,
authorization requirements, limitations, and enabling-project references.
Helen consumes ownership, qualification, adapter/wrapper presence, fresh
health/capacity, implementation requirements, and gap state. The lifecycle is:

capability inquiry -> assessment -> gap if any -> specification -> enabling
project -> registration -> re-evaluation -> Grace resumption

If no qualified worker exists, Helen returns a capability-gap proposal with
required skills, bootstrap dependencies, evidence deadline, prohibited claims,
and a statement that it does not authorize implementation or execution.

Stop and return to the Steward or Chief Architect for unresolved ownership,
classification, credentials, network boundary, institutional acceptance, new
authority model, registry replacement, protected data, missing bootstrap
capability, or required live service outside the package. Never invent defaults,
reuse failed IDs/paths, bypass validators, or turn a test into acceptance.

