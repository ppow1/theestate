# ESTATE-CAP-001 — Canonical Resident Capability / Adapter Template and Runbook

## Objective

Create the Estate-wide canonical framework for adding a new capability, tool, provider, or local execution adapter to any resident or department.

This is not Engineering-only documentation. The resulting framework must support repeated use across the Estate, including but not limited to:

- Engineering;
- Historian;
- Legal Expert;
- Grace;
- Helen;
- media and image-generation residents;
- transcription and speech systems such as Whisper;
- local text and code models such as Qwen Coder;
- ComfyUI and other bounded local services;
- future specialist residents with resident-owned toolsets.

The Estate already has working examples in Qwen, Codex, PTM readiness, Dispatch, provider receipts, reconciliation, replay protection, and governed technical intake. This work package must extract those lessons into a reusable Estate-wide standard rather than recreating another provider implementation.

## Governing design principle

Use a two-layer model:

1. **Estate Core Capability Contract** — common across every resident and department.
2. **Resident / Provider Overlay** — the resident-specific authority, evidence, lifecycle, and output requirements.

Do not create separate unrelated onboarding systems for Engineering, Historian, Legal, media, speech, or other residents.

The common framework must be sufficiently general to support:

- execution providers;
- research and retrieval tools;
- legal or historical source-analysis tools;
- transcription and media processors;
- image-generation systems;
- code-generation and repository tools;
- classification, audit, and validation tools;
- read-only and write-capable tools;
- local-only and externally networked tools.

## Required deliverables

### 1. Estate-wide capability onboarding standard

Create a canonical architecture document comparable to:

`docs/architecture/Estate_Resident_Capability_and_Adapter_Onboarding_Standard.md`

It must define:

- capability identity and ownership;
- resident or department ownership;
- provider identity;
- adapter identity and version;
- implementation kind;
- authority boundary;
- classification ceiling;
- network boundary;
- model/runtime/service identity;
- capability inputs and outputs;
- health, capacity, qualification, authorization, and freshness evidence;
- exact read/write/output scope;
- prompt, source, or request provenance;
- artifact and receipt contracts;
- failure, timeout, cancellation, and partial-output handling;
- replay and idempotency;
- schema requirements;
- testing and live acceptance;
- registration, synchronization, rollback, deprecation, and removal;
- institutional acceptance separation.

The document must clearly distinguish:

- a capability definition;
- a provider declaration;
- an adapter implementation;
- a resident authorization;
- a Dispatch or execution authorization;
- a successful execution;
- institutional acceptance.

### 2. Canonical implementation template

Create a fill-in template comparable to:

`collaboration/work_packages/templates/RESIDENT_CAPABILITY_AND_ADAPTER_IMPLEMENTATION_TEMPLATE.md`

The template must be usable to commission implementation of a new capability or adapter.

It must include sections for:

- problem statement;
- resident / department owner;
- requested capability;
- capability taxonomy;
- provider and adapter identity;
- runtime/service/model binding;
- existing source-of-truth surfaces;
- authority and governance boundaries;
- allowed inputs;
- allowed reads;
- allowed writes;
- expected outputs;
- artifact contract;
- provider receipt contract;
- evidence requirements;
- health and capacity;
- freshness and expiry;
- prompt/request/source provenance;
- network and endpoint policy;
- data classification;
- credentials and secret handling;
- execution limits;
- timeout and cancellation;
- failure evidence;
- collision behavior;
- idempotency and replay;
- schema additions or changes;
- registration and catalog changes;
- resident manifest changes;
- PTM / readiness dependencies where applicable;
- Dispatch / handoff integration where applicable;
- reconciliation and terminal evidence;
- unit tests;
- integration tests;
- negative tests;
- live governed acceptance;
- runtime synchronization;
- operator documentation;
- deprecation / rollback;
- completion criteria;
- explicit prohibited behavior.

The template must support both:

- provider-backed executable capabilities; and
- resident-owned non-execution tools such as legal research, historical retrieval, source comparison, or evidence analysis.

### 3. Operator runbook

Create a canonical runbook comparable to:

`docs/operations/Resident_Capability_and_Adapter_Onboarding_Runbook.md`

The runbook must describe the actual sequence an operator follows from request to accepted operational capability.

Required phases:

1. Request and classify the capability.
2. Identify the resident or department owner.
3. Search for an existing capability/provider/adapter before creating a new one.
4. Decide whether this is:
   - an existing adapter registration;
   - a new provider configuration;
   - a new adapter implementation;
   - a resident-specific tool wrapper;
   - a capability-gap enabling project.
5. Define authority and classification boundaries.
6. Define source, prompt, request, or evidence provenance.
7. Define exact input, read, write, and output contracts.
8. Define health, qualification, capacity, authorization, and freshness evidence.
9. Define schemas and durable records.
10. Implement provider/adapter or resident-tool wrapper.
11. Register capability and provider.
12. Connect resident discovery and capability assessment.
13. Connect readiness / PTM / Dispatch / handoff only where required.
14. Add receipts, artifacts, reconciliation, and terminal evidence.
15. Run unit and integration validation.
16. Run negative/fail-closed validation.
17. Run one fresh live governed acceptance task.
18. Publish an operational baseline entry.
19. Synchronize installed runtimes if required.
20. Declare exact operational scope and deferred backlog.

The runbook must include decision tables answering:

- When is a provider catalog entry sufficient?
- When is an execution adapter required?
- When is a resident-owned tool wrapper sufficient?
- When is PTM readiness required?
- When is Dispatch required?
- When is a provider receipt required?
- When is live acceptance mandatory?
- When may a capability remain designed but not operational?
- What constitutes a safe stop condition?

### 4. Canonical checklist

Create a concise checklist comparable to:

`docs/operations/checklists/Resident_Capability_Adapter_Readiness_Checklist.md`

The checklist must be usable during review and merge readiness.

At minimum it must cover:

- no duplicate capability;
- stable IDs and versions;
- resident ownership;
- authority boundaries;
- classification ceiling;
- endpoint/network restrictions;
- exact scopes;
- prompt/source provenance;
- closed schemas;
- canonical records;
- create-once persistence;
- failure evidence;
- replay protection;
- receipt/artifact hashes;
- runtime registration;
- capability discovery;
- health/capacity/freshness evidence;
- negative tests;
- live acceptance;
- operator documentation;
- rollback/deprecation;
- institutional acceptance remains separate.

### 5. Resident capability manifest contract

Determine whether the Estate already has one canonical resident capability/tool manifest.

If one exists:

- document and reuse it;
- do not create a duplicate registry.

If no complete canonical manifest exists:

- define the smallest versioned resident capability-manifest contract necessary to let a resident such as Helen, Historian, Legal Expert, or Engineering enumerate:
  - capabilities;
  - provider/tool bindings;
  - adapter identities;
  - operational status;
  - health/capacity evidence sources;
  - authorization requirements;
  - classification ceilings;
  - accepted inputs and outputs;
  - current limitations.

Any manifest schema must be closed, versioned, and compatible with the existing provider catalog rather than replacing it.

### 6. Example overlays

Create at least four short worked examples demonstrating how the common template changes by resident/tool class:

1. **Qwen Coder / Engineering execution**
   - bounded repository implementation;
   - exact worktree/write/output scopes;
   - provider receipt;
   - Dispatch and reconciliation.

2. **Whisper / transcription service**
   - bounded input media;
   - local service/model identity;
   - transcript artifact;
   - timestamps/language/model evidence;
   - no repository implementation authority.

3. **ComfyUI / image generation**
   - workflow provenance;
   - model and node dependencies;
   - image artifact and metadata;
   - health/capacity evidence;
   - no automatic acceptance of generated media.

4. **Historian or Legal Expert research tool**
   - source provenance;
   - citation and evidence chain;
   - read-only authority by default;
   - jurisdiction/date/source limitations for Legal;
   - uncertainty and conflict reporting;
   - no silent substitution of model inference for source evidence.

These are examples only. Do not implement Whisper, Qwen Coder, ComfyUI live execution, Historian, or Legal tools in this work package.

## Reuse requirements

Read and reconcile the existing accepted work before authoring the standard:

- Engineering Operational Baseline;
- Qwen local provider documentation and schemas;
- Codex execution adapter documentation and schemas;
- provider catalog and capability definitions;
- Helen capability assessment and provider-selection surfaces;
- PTM readiness contracts;
- Engineering commission and authorization contracts;
- Operations decision contracts;
- Dispatch and adapter-request contracts;
- provider receipt schemas;
- reconciliation and Grace terminal receipt behavior;
- ComfyUI service/provider manifests;
- resident manifests or readiness surfaces already present;
- any existing onboarding, tool registry, workforce, or adapter runbooks.

Do not create:

- a second provider catalog;
- a second capability registry;
- a second Dispatch path;
- a second PTM readiness system;
- a second resident personnel system;
- provider-specific copies of common authority contracts.

## Generalization requirements

The framework must explicitly support three layers:

### Estate core

Common capability, provider, adapter, authority, evidence, receipt, and lifecycle rules.

### Resident overlay

Resident-specific ownership, reasoning, safety, source, and escalation rules.

Examples:

- Engineering: worktree/write/output authority;
- Historian: archival provenance and source conflict;
- Legal Expert: jurisdiction, effective date, citation, and non-advice boundaries;
- Grace: objective/action and operator communication;
- Helen: workforce/capability availability and hiring/enabling-project logic.

### Provider/tool overlay

Technical details of the model, binary, service, endpoint, workflow, or executable wrapper.

Examples:

- Qwen Coder;
- Whisper;
- ComfyUI;
- database/search connector;
- OCR or document parser;
- local Python tool;
- external API.

## Validation requirements

Validate that the resulting documents and templates are internally consistent with the current repository.

At minimum:

- confirm every referenced canonical surface exists;
- identify any unresolved ownership ambiguity;
- verify template sections cover both execution and non-execution tools;
- walk through all four examples using the template;
- confirm no duplicate registry or lifecycle is proposed;
- confirm the runbook reaches a testable operational state;
- confirm institutional acceptance remains separate;
- run Markdown/link/reference checks available in the repository;
- run `git diff --check`;
- keep the worktree clean after commit.

## Branch and PR

Create a fresh branch from current main:

`architecture/resident-capability-adapter-standard`

Commit all deliverables, push, and open a draft PR against main.

Do not merge.

## Final report

Report:

- starting main HEAD;
- branch and final HEAD;
- files created or changed;
- canonical surfaces reused;
- whether a resident capability manifest already existed;
- any schema created or changed;
- how the Estate core / resident overlay / provider overlay model is represented;
- example overlays completed;
- validation performed;
- unresolved architecture decisions;
- draft PR number;
- exact next Steward action.
