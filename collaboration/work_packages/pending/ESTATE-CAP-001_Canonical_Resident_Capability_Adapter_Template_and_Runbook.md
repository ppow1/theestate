# ESTATE-CAP-001 — Canonical Estate Capability Onboarding Standard, Template, and Runbook

## Objective

Create the Estate-wide canonical framework for adding a new capability, tool, provider, resident-owned wrapper, or local execution adapter to any resident or department.

The result must be executable by the Engineering Department rather than being written for one implementation worker. It must be usable by:

- Grace;
- Helen;
- Codex CLI;
- Qwen Coder or another local coding model;
- a future Engineering resident;
- a human engineer;
- any other governed implementation worker that satisfies the required capability contract.

The documents must not assume Codex-specific commands, behavior, memory, or authority except inside a clearly labeled Codex example overlay.

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

The Estate already has working examples in Qwen, Codex, PTM readiness, Dispatch, provider receipts, reconciliation, replay protection, governed technical intake, capability-gap handling, and operational baselines. This work package must extract those lessons into a reusable Estate-wide standard rather than recreating another provider implementation.

## Governing design principle

Use a three-layer model:

1. **Estate Core Capability Contract** — common capability, provider, adapter, authority, evidence, lifecycle, receipt, replay, and acceptance rules.
2. **Resident Overlay** — resident-specific ownership, safety, reasoning, source, escalation, and acceptance rules.
3. **Provider / Tool Overlay** — technical details of the model, binary, service, endpoint, workflow, connector, or executable wrapper.

Do not create separate unrelated onboarding systems for Engineering, Historian, Legal, media, speech, or other residents.

The framework must support:

- execution providers;
- research and retrieval tools;
- legal or historical source-analysis tools;
- transcription and media processors;
- image-generation systems;
- code-generation and repository tools;
- classification, audit, and validation tools;
- read-only and write-capable tools;
- local-only and externally networked tools;
- model-backed, binary-backed, service-backed, connector-backed, and human-backed implementation workers.

## Executor-neutral implementation requirement

The canonical implementation template and runbook must be complete enough that a governed implementation worker can execute a new onboarding package without hidden oral context.

A valid onboarding package must explicitly provide or require discovery of:

- repository and branch/worktree;
- current canonical source-of-truth records;
- resident or department owner;
- requested capability and maturity target;
- provider and adapter identity;
- runtime/service/model binding;
- exact authority boundaries;
- exact input, read, write, and output scopes;
- schemas and persistent records;
- registration points;
- evidence and freshness rules;
- validation commands;
- live acceptance scenario;
- rollback and deprecation behavior;
- merge and synchronization boundaries;
- explicit stop conditions and decisions reserved to the Steward or Chief Architect.

The package must not depend on an implementer guessing:

- where records belong;
- which registry is canonical;
- which runtime is authoritative;
- what constitutes success;
- whether live execution is authorized;
- whether institutional acceptance is implied;
- which failures are correctable and which require Steward authority.

The standard must include a self-check section that an implementation worker completes before coding and a closure report format that any worker can produce after implementation.

## Capability maturity model

Define and adopt one Estate-wide maturity model for capabilities. Use these levels unless direct repository evidence requires different names:

### Level 0 — Concept

- Need identified.
- No canonical capability registration.
- No provider or tool binding.
- Not dispatchable.

### Level 1 — Registered

- Capability identity and owner are canonical.
- Inputs, outputs, classification, and authority boundaries are defined.
- No operational provider is required yet.
- Not dispatchable for live execution.

### Level 2 — Provider Available

- One or more provider/tool candidates are registered.
- Adapter or wrapper may be designed or partially implemented.
- Health, qualification, authorization, or readiness may be incomplete.
- Not dispatchable unless a separate approved non-execution path exists.

### Level 3 — Governed

- Provider/adapter or resident-tool wrapper is implemented.
- Required schemas, authority propagation, evidence, receipts, replay, failure behavior, and tests exist.
- Governed dry-run or bounded acceptance may be possible.
- Live dispatch is allowed only where the capability record explicitly authorizes it.

### Level 4 — Operational

- Fresh live governed acceptance has passed.
- Operator runbook and runtime synchronization are complete.
- Exact accepted scope and prohibitions are published.
- Grace/Helen and the owning resident can discover and route the capability under policy.

### Level 5 — Institutionally Accepted

- Institutional authority has explicitly accepted the capability for its recorded scope.
- Acceptance is separately recorded and never inferred from successful execution.

The standard must define:

- required evidence for entering each level;
- prohibited behavior at each level;
- who may authorize each transition;
- how regression or evidence expiry can reduce current dispatchability without rewriting historical maturity evidence;
- how Helen and residents report maturity and current availability separately;
- how Grace explains a capability that exists but is not yet dispatchable.

## Required deliverables

### 1. Estate-wide capability onboarding standard

Create:

`docs/architecture/Estate_Capability_Onboarding_Standard.md`

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
- maturity levels and transition authority;
- institutional acceptance separation.

The document must clearly distinguish:

- a capability definition;
- a provider declaration;
- an adapter implementation;
- a resident authorization;
- a Dispatch or execution authorization;
- a successful execution;
- operational status;
- institutional acceptance.

### 2. Canonical implementation work-package template

Create:

`collaboration/work_packages/templates/ESTATE_CAPABILITY_ONBOARDING_IMPLEMENTATION_TEMPLATE.md`

The template must be usable to commission implementation by any qualified Engineering worker. It must not be Codex-specific.

Required sections:

- package identity and requested maturity target;
- problem statement;
- resident / department owner;
- requested capability;
- capability taxonomy;
- provider and adapter identity;
- runtime/service/model binding;
- implementation-worker capability requirements;
- existing source-of-truth surfaces;
- authority and governance boundaries;
- allowed inputs;
- allowed reads;
- allowed writes;
- expected outputs;
- artifact contract;
- provider/tool receipt contract;
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
- explicit prohibited behavior;
- Steward-stop conditions;
- final closure report format.

The template must support both:

- provider-backed executable capabilities; and
- resident-owned non-execution tools such as legal research, historical retrieval, source comparison, evidence analysis, classification, and advisory workflows.

The template must include fill-in placeholders, examples of acceptable values, and a completeness checklist so a worker can detect missing authority before implementation.

### 3. Operator and implementation runbook

Create:

`docs/operations/Estate_Capability_Onboarding_Runbook.md`

The runbook must describe the actual sequence from request to accepted operational capability.

Required phases:

1. Request and classify the capability.
2. Identify the resident or department owner.
3. Search for an existing capability/provider/adapter before creating a new one.
4. Select the requested maturity target.
5. Decide whether the work is:
   - existing adapter registration;
   - new provider configuration;
   - new adapter implementation;
   - resident-specific tool wrapper;
   - capability-gap enabling project;
   - evidence or qualification work only.
6. Define authority and classification boundaries.
7. Define source, prompt, request, or evidence provenance.
8. Define exact input, read, write, and output contracts.
9. Define health, qualification, capacity, authorization, and freshness evidence.
10. Define schemas and durable records.
11. Identify the qualified implementation worker through Helen.
12. Implement provider/adapter or resident-tool wrapper.
13. Register capability and provider.
14. Connect resident discovery and capability assessment.
15. Connect readiness / PTM / Dispatch / handoff only where required.
16. Add receipts, artifacts, reconciliation, and terminal evidence.
17. Run unit and integration validation.
18. Run negative/fail-closed validation.
19. Run one fresh live governed acceptance task where the target level requires it.
20. Publish an operational baseline entry.
21. Synchronize installed runtimes if required.
22. Declare exact operational scope, maturity level, and deferred backlog.

The runbook must include decision tables answering:

- When is a capability definition sufficient?
- When is a provider catalog entry sufficient?
- When is an execution adapter required?
- When is a resident-owned tool wrapper sufficient?
- When is PTM readiness required?
- When is Dispatch required?
- When is a provider/tool receipt required?
- When is live acceptance mandatory?
- When may a capability remain designed but not operational?
- What constitutes a safe stop condition?
- Which worker capabilities are required to implement each class of onboarding?
- When must Helen create an enabling-project proposal because no qualified implementation worker exists?

### 4. Canonical readiness and review checklist

Create:

`docs/operations/checklists/Estate_Capability_Onboarding_Readiness_Checklist.md`

At minimum it must cover:

- no duplicate capability;
- stable IDs and versions;
- resident ownership;
- maturity level and transition authority;
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
- institutional acceptance remains separate;
- implementation worker did not exceed package authority.

### 5. Resident capability manifest contract

Determine whether the Estate already has one canonical resident capability/tool manifest.

If one exists:

- document and reuse it;
- do not create a duplicate registry.

If no complete canonical manifest exists:

- define the smallest versioned resident capability-manifest contract necessary to enumerate:
  - capabilities;
  - maturity level;
  - current availability;
  - provider/tool bindings;
  - adapter identities;
  - operational status;
  - health/capacity evidence sources;
  - authorization requirements;
  - classification ceilings;
  - accepted inputs and outputs;
  - current limitations;
  - implementation-worker requirements where an enabling project is needed.

Any manifest schema must be closed, versioned, and compatible with the existing provider catalog rather than replacing it.

### 6. Grace and Helen consumption contract

Document how Grace and Helen consume the standard.

Grace must be able to determine and communicate:

- whether the capability exists;
- its maturity level;
- whether it is currently available;
- whether it is currently dispatchable;
- what authorization is required;
- whether an enabling project is blocking the original request;
- whether the request can resume after onboarding.

Helen must be able to determine:

- whether the Estate has a qualified worker/provider/tool;
- whether current evidence is fresh;
- whether an adapter or wrapper already exists;
- whether a new implementation worker or enabling project is required;
- what implementation capabilities are necessary;
- when to return a capability-gap proposal to Grace.

The documents must preserve the established lifecycle:

`capability inquiry → assessment → gap if any → specification → enabling project → registration → re-evaluation → Grace resumption`.

### 7. Worked example overlays

Create at least four worked examples using the canonical template:

1. **Qwen Coder / Engineering execution**
   - bounded repository implementation;
   - exact worktree/write/output scopes;
   - provider receipt;
   - Dispatch and reconciliation;
   - implementation-worker requirements suitable for Codex, Qwen Coder, or a human engineer.

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

The examples are designs only. Do not implement Whisper, Qwen Coder, ComfyUI live execution, Historian, or Legal tools in this work package.

### 8. Machine-checkable package linting

Determine whether the current work-package validator can enforce required onboarding sections.

If it can be extended within bounded scope, add validation for the canonical onboarding template so incomplete packages fail before dispatch.

At minimum validate the presence of:

- owner;
- capability ID;
- target maturity level;
- provider/adapter or tool-wrapper disposition;
- authority boundaries;
- exact scopes or explicit not-applicable declarations;
- evidence requirements;
- test plan;
- live acceptance requirement or explicit exemption;
- rollback/deprecation plan;
- Steward-stop conditions.

Do not create a second work-package validation system.

## Reuse requirements

Read and reconcile:

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
- existing onboarding, tool registry, workforce, and adapter runbooks;
- capability-gap and enabling-project records.

Do not create:

- a second provider catalog;
- a second capability registry;
- a second Dispatch path;
- a second PTM readiness system;
- a second resident personnel system;
- provider-specific copies of common authority contracts;
- an implementation-worker-specific onboarding system.

## Validation requirements

Validate that the resulting standard can be followed by Grace, Helen, Codex, Qwen Coder, another qualified Engineering worker, or a human without hidden context.

At minimum:

- confirm every referenced canonical surface exists;
- identify unresolved ownership ambiguity;
- verify template sections cover execution and non-execution tools;
- walk through all four examples using the template;
- perform one paper exercise where Helen identifies required implementation-worker capabilities and Grace receives an enabling-project proposal;
- perform one paper exercise where the capability is already Level 4 and Grace resumes the original request without new implementation;
- confirm no duplicate registry or lifecycle is proposed;
- confirm the runbook reaches a testable maturity state;
- confirm institutional acceptance remains separate;
- confirm the documents contain no Codex-only assumptions outside examples;
- run available Markdown/link/reference checks;
- run work-package validation, including new linting if added;
- run `git diff --check`;
- keep the worktree clean after commit.

## Branch and PR

Create a fresh branch from current main:

`architecture/estate-capability-onboarding-standard`

Commit all deliverables, push, and open a draft PR against main.

Do not merge.

## Final report

Report:

- starting main HEAD;
- branch and final HEAD;
- files created or changed;
- canonical surfaces reused;
- whether a resident capability manifest already existed;
- schemas created or changed;
- maturity model adopted;
- how executor-neutral implementation is ensured;
- how Grace and Helen consume the standard;
- whether work-package linting was added;
- example overlays completed;
- validation performed;
- unresolved architecture decisions;
- draft PR number;
- exact next Steward action.
