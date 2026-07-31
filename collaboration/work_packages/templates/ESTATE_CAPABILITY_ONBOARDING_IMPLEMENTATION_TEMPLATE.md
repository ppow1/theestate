# ESTATE-CAPABILITY-<NNN> — Implementation Package

Status: Draft / Ready / In Progress / Blocked / Complete
Package ID: <stable ID>
Requested maturity: <0 Concept | 1 Registered | 2 Provider Available | 3 Governed | 4 Operational | 5 Institutionally Accepted>
Owner: <resident or department>
Reserved decision reference: <path/id/digest or N/A rationale>

## Problem, owner, and discovery

- Problem/request: <bounded acceptance-testable statement>
- Resident/department owner: <canonical owner>
- Capability ID/version: <capability_id>@<version>
- Taxonomy: <execution/research/retrieval/transcription/media/image/classification/audit/advisory>
- Existing capability/provider/adapter search: <paths, queries, result>
- Duplicate decision: <reuse existing | new with reason>

## Provider, adapter, or resident tool

- Disposition: <existing adapter | provider config | new adapter | resident wrapper | enabling project | evidence only>
- Provider ID/type/implementation kind: <catalog values or N/A>
- Adapter/tool ID/version: <registered identity or N/A>
- Runtime/service/model binding: <exact identity, version, endpoint>
- Worker requirements and Helen qualification evidence: <skills, tools, classification, tests>
- Bootstrap capabilities and dependencies: <explicit; capability being created cannot bootstrap itself>

## Authority and safety

- Allowed authority: <exact operation>
- Prohibited authority: <shell, merge, acceptance, arbitrary writes, etc.>
- Classification ceiling: <public/internal/restricted/protected>
- Resident authorization: <record/reference>
- PTM/readiness: <reference or not_applicable rationale>
- Dispatch/final handoff: <reference or not_applicable rationale>
- Network/endpoint policy: <loopback/allowlist/offline/connector policy>
- Credentials/secrets: <secret store and redaction; never commit>

## Exact contracts and provenance

- Allowed inputs: <types, IDs, size/count limits>
- Prompt/request/source provenance: <canonical source, type, digest, originator, freshness>
- Allowed reads: <exact repository-relative paths or not_applicable rationale>
- Allowed writes: <exact paths or not_applicable rationale>
- Expected outputs: <exact artifact/receipt paths or bounded external sinks>
- Artifact contract: <format, metadata, digest, validation>
- Provider/tool receipt: <schema/path, required fields, no secrets/full prompt>
- Collision: <create-once, equivalent replay, conflict failure>
- Timeout/cancellation/partial output: <deadline and truthful state>

## Evidence and durable records

- Health, capacity, qualification, authorization, and freshness sources:
  <source, observation, scope, expiry>
- Replay/idempotency key: <deterministic identity and conflict rule>
- New/changed closed schemas and records: <paths, IDs, versions>
- Persistence: <canonical namespace, create-once, complete write, fsync/durability>
- Registration/catalog/capability source/resident manifest changes: <exact paths>
- Runtime synchronization: <installed package/service/model evidence>

## Validation and acceptance

- Unit tests: <exact paths/commands>
- Integration tests: <exact lifecycle/registry commands>
- Negative tests: <missing authority, bad scope, stale evidence, mismatch, collision, replay>
- Live governed acceptance: <required or explicit lower-level exemption>
- Acceptance scenario and fresh IDs/paths: <bounded task>
- Reconciliation and terminal evidence: <records>
- Operator documentation: <runbook/baseline paths>

## Rollback, deprecation, and completion

- Reversible units: <commits, registrations, records>
- Rollback authority and exact steps: <owner>
- In-flight work: <cancel/drain/quarantine behavior>
- Deprecation/removal: <supersession, queue drain, historical evidence>
- Completion criteria: <all evidence and test results>
- Closure report: <path and required fields>

## Explicit prohibited behavior and stop conditions

Do not live-execute before the target and authority allow it, broaden scopes,
add provider-created paths, copy secrets, bypass Grace/Helen/PTM/Dispatch/
handoff, replace a canonical registry, reuse failed IDs/outputs, claim
institutional acceptance, modify protected data, or use a missing capability
as its own bootstrap.

Stop for unresolved owner, classification, credential, endpoint, schema,
worker qualification, dependency, or reserved authority. Return a bounded gap
to Helen/Grace or the Steward; do not invent policy.

## Completeness checklist

- [ ] Owner, capability ID/version, taxonomy, target maturity.
- [ ] Existing registry/adapter search and duplicate decision.
- [ ] Provider/adapter/wrapper disposition and worker requirements.
- [ ] Authority, classification, network, credentials, prohibitions.
- [ ] Inputs, reads, writes, outputs, provenance, artifact, receipt.
- [ ] Health, capacity, qualification, authorization, freshness.
- [ ] PTM/Dispatch dependencies or explicit N/A rationale.
- [ ] Closed schemas, persistence, registration, synchronization.
- [ ] Unit, integration, negative, replay/collision, and acceptance plan.
- [ ] Rollback, deprecation, stop conditions, closure report.

## Closure report format

Report package ID, owner, target/achieved maturity, branch/commit/PR, files and
records changed, provider/adapter/tool, exact accepted scope, evidence freshness,
tests and acceptance, artifact/receipt digests, failures/limitations, runtime
sync, rollback/deprecation, availability, institutional acceptance separately,
live provider/model changes, historical-evidence changes, and the next Steward
decision. For a non-execution research/legal/history/classification tool, mark
PTM/Dispatch/adapter N/A only with rationale and retain owner authorization,
read-only scope, provenance, evidence chain, uncertainty, receipt, tests, and
deprecation.

