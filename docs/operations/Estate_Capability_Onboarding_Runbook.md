# Estate Capability Onboarding Runbook v1

Use this with the Estate Capability Onboarding Standard and implementation
template. It is executable by Grace, Helen, Codex CLI, Qwen Coder, another
qualified worker, or a human engineer.

## Request-to-operation sequence

1. Request and classify the capability: execution, research, retrieval,
   transcription, media, image, classification, validation, or advisory.
2. Identify the resident/department owner and technical accountability owner.
3. Search data/registry/capabilities.json, config/providers/catalog.json,
   existing resident manifests, service manifests, adapters, and the read-only
   capability registry before creating anything.
4. Select Level 0-5 and record the evidence and transition authority.
5. Classify the work as existing registration, provider config, new adapter,
   resident wrapper, enabling project, or evidence/qualification only.
6. Define authority, classification, network, credentials, prohibitions, and
   reserved decisions.
7. Define source/prompt/request/evidence provenance and freshness.
8. Define exact inputs, reads, writes, outputs, artifacts, receipts, hashes,
   timeout, cancellation, partial-output, and collision behavior.
9. Define separate health, capacity, qualification, authorization, and expiry
   evidence for the same subject and scope.
10. Define/reuse closed schemas and canonical create-once durable records.
11. Helen identifies a qualified implementation worker and records requirements.
   If none exists, return a capability-gap/enabling-project proposal.
12. Implement within package authority; the capability being created is never
   its own bootstrap.
13. Register through existing provider catalog, capability source, resident
   manifest, service manifest, and adapter registry surfaces.
14. Connect Grace discovery and Helen assessment without a second registry.
15. Connect PTM/readiness, Engineering authorization, Operations decision,
   Dispatch, and final handoff only for applicable technical execution.
16. Publish artifact, receipt, validation, reconciliation, and terminal evidence.
17. Run unit, schema, integration, negative, replay, collision, cancellation,
   and network/path boundary tests.
18. Run one fresh governed live acceptance when Level 4 requires it.
19. Publish an operational baseline with exact scope, prohibitions, maturity,
   availability, limitations, runtime, and backlog.
20. Synchronize installed runtimes/services/models and record evidence.
21. Close with separate execution, validation, integration, operational-status,
   and institutional-acceptance statements.

## Decision table

| Question | Answer |
|---|---|
| Definition sufficient? | Level 1 only: identity, owner, taxonomy, I/O, classification, boundaries; no dispatch. |
| Catalog entry sufficient? | Level 2 declaration only; not qualification, health, authority, or execution. |
| Adapter required? | Any executable provider-backed path or runtime side effect. |
| Resident wrapper sufficient? | Read-only advisory/research/source/classification workflows with owner authorization and receipt. |
| PTM required? | Dependency-changing project or Engineering execution; not mere description. |
| Dispatch required? | Bounded technical execution using an adapter or changing governed state. |
| Receipt required? | Every provider/tool invocation or material advisory result. |
| Live acceptance mandatory? | Level 4; exemption requires explicit lower-level/non-execution rationale. |
| Designed but non-operational? | Any incomplete implementation, evidence, registration, freshness, or acceptance. |
| Safe stop? | Missing owner, scope, schema, evidence, worker, bootstrap, credential, network, or reserved authority. |
| Worker capabilities? | Adapter: coding, schema, persistence, tests, runtime/security. Research: source analysis, provenance, classification, uncertainty. Media: format/workflow/model evidence. |
| No qualified worker? | Helen returns a capability-gap proposal; Grace may propose a separate enabling project. |

## Grace and Helen consumption

Grace communicates existence, maturity, current availability,
dispatchability, authorization requirements, limitations, and enabling-project
state. Helen evaluates declared -> qualified -> healthy -> available ->
authorized with fresh evidence for one scope. Registration does not skip
re-evaluation. The lifecycle remains:

capability inquiry -> assessment -> gap if any -> specification -> enabling
project -> registration -> re-evaluation -> Grace resumption

Use fresh IDs and create-once paths for each acceptance. Never call a provider
directly, widen a scope to pass a test, infer authority from a filename, reuse
failed evidence, or call operational success institutional acceptance.

## Safe stop and reserved decisions

Return to the Steward or Chief Architect for unresolved ownership,
classification, credentials, network boundary, protected data, institutional
acceptance, new authority model, registry replacement, missing bootstrap, or a
required live service outside the package.

