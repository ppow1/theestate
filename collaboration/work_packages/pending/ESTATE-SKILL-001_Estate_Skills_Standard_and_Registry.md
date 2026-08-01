# ESTATE-SKILL-001 — Estate Skills Standard and Registry

Status: Pending
Owner: Estate Architecture with Grace, Helen, PTM, Engineering, and resident owners
Execution class: architecture, schema, registry, validation, documentation; no automatic broad operational authority

## Objective

Introduce a canonical Estate Skill layer for reusable governed procedures that combine existing capabilities, providers, tools, resident authority, evidence, and lifecycle steps into repeatable operational outcomes.

A Skill is not a capability, provider, resident, work package, or unrestricted script. It is a versioned governed procedure that declares what it does, what capabilities it requires, who owns it, how it is invoked, what authority it needs, what it may read/write, how it stops, and what evidence proves completion.

## Required architectural distinctions

The standard must preserve these distinctions:

- Resident: accountable actor or institutional role.
- Capability: an ability the Estate may possess.
- Provider/tool/adapter: a concrete implementation mechanism.
- Skill: a reusable governed procedure coordinating capabilities.
- Work package: a bounded assignment to implement, change, test, or operate something.
- Automation: scheduled or condition-triggered invocation of an already governed skill.

Skills never create authority merely by being registered. Provider availability never makes a Skill executable. Institutional acceptance remains separate.

## Required deliverables

1. Estate Skill Standard
2. Closed versioned Skill manifest schema
3. Canonical Skill registry and read-only aggregation behavior
4. Skill authoring template
5. Skill onboarding and review runbook
6. Skill readiness checklist
7. Skill invocation, execution, receipt, and reconciliation contract
8. Grace and Helen integration rules
9. Maturity and availability model
10. Worked examples without unauthorized live implementation
11. First implementation: read-only Repository Health skill

## Skill manifest contract

At minimum declare:

- skill_id, version, name, short Steward aliases;
- owner resident/department and technical maintainer;
- purpose and supported outcomes;
- trigger classes: interactive, scheduled, event-driven, diagnostic, execution;
- required capabilities and minimum maturity;
- allowed providers/tools/adapters and selection policy;
- bootstrap dependencies;
- classification ceiling and data handling;
- required authority and reserved decisions;
- inputs, exact/bounded reads, writes, outputs, external sinks;
- ordered stages and decision points;
- preconditions, readiness, evidence freshness, and health requirements;
- stop, escalation, cancellation, timeout, and partial-result behavior;
- idempotency/replay identity and conflict handling;
- artifact, receipt, validation, reconciliation, and terminal result contracts;
- rollback/deprecation/supersession behavior;
- current maturity, current availability, and institutional acceptance separately;
- plain-English examples of what the Steward may say.

Schemas must reject absolute/traversing repository references, hidden authority, undeclared provider-created paths, broad wildcards without bounded policy, unresolved placeholders, and missing stop conditions.

## Maturity model

Define a Skill maturity model compatible with the Estate capability maturity model, for example:

0. Concept
1. Registered
2. Dependencies Available
3. Governed
4. Operational
5. Institutionally Accepted

Historical maturity and current dispatchability must be reported separately. A Level 4 Skill can be temporarily unavailable because a required capability, provider, credential, or evidence source is stale.

## Grace behavior

Grace must be able to:

- discover Skills by plain language, formal name, alias, owner, or outcome;
- explain what a Skill does and does not do;
- create a bounded objective/action invoking the Skill;
- preserve the Steward's words as canonical request provenance;
- request missing authority rather than invent it;
- report progress, blocks, failure, and completion truthfully;
- avoid invoking a Skill when dependencies or authority are unavailable;
- suggest a relevant Skill without silently executing it.

## Helen behavior

Helen must assess:

- Skill existence and version;
- owner authorization;
- required capability availability and maturity;
- qualified implementation/execution worker;
- provider/tool health, capacity, and freshness;
- bootstrap dependencies;
- current dispatchability;
- gaps and enabling projects.

Helen must return a bounded gap when a Skill exists but cannot currently run.

## Runtime and governance

Reuse existing Estate lifecycle and registry surfaces where appropriate. Do not create a parallel capability registry, parallel PTM, parallel Dispatch, or parallel authority system.

A technical execution Skill must flow through the applicable canonical chain, including Grace, Helen, PTM, Engineering/owner authorization, Operations decision, Dispatch, adapter/tool execution, receipt, validation, reconciliation, and terminal response.

A non-execution diagnostic or advisory Skill may use a reduced path only when explicitly documented, while retaining owner authorization, provenance, receipt, and truthful completion.

## First operational Skill: Repository Health

Implement a read-only Level 4 candidate Skill with memorable aliases such as:

- Check Git
- Repo Health
- Is Git clean?

It must:

- identify the canonical repository and approved worktrees;
- fetch remotes only when authorized and safe;
- report branch, HEAD, upstream, ahead/behind/divergence;
- report clean/dirty status and classify tracked/untracked/ignored content;
- list worktrees, local branches with unique commits, stale branch references, and stashes;
- identify startup/runtime references to noncanonical trees;
- report synchronization risks;
- write one bounded report and receipt;
- make no commit, push, reset, checkout, stash, prune, delete, or file modification.

The read-only Skill must not expose secrets or include full sensitive diffs by default.

## Worked examples

Provide design examples for:

- Sync GitHub — governed commit/push preparation and execution;
- Clean Git — worktree/stash reconciliation with Steward checkpoints;
- Add a Tool — capability onboarding Skill invoking the existing onboarding standard;
- Promote Runtime — blue/green validation, promotion, and rollback;
- Transcribe and File — Whisper plus resident filing/provenance;
- Generate Image — ComfyUI request, workflow provenance, and artifact receipt;
- Verify Sources — Historian source review;
- Check Citation — Legal source/citation verification.

Do not live-enable these examples unless separately authorized.

## Testing

Include:

- schema and lint tests;
- alias uniqueness and ambiguity tests;
- capability dependency resolution tests;
- unavailable/stale dependency tests;
- missing authority and prohibited scope tests;
- replay/conflict tests;
- diagnostic versus execution boundary tests;
- Grace discovery and plain-language matching tests;
- Helen assessment and gap tests;
- receipt/reconciliation tests;
- Repository Health live governed read-only acceptance.

## Operator documentation

The runbook must explain:

- how to ask Grace to use a Skill;
- how to ask what Skills exist;
- how to request proposal-only versus execute-now;
- how to inspect required authority and scope;
- how to stop/cancel;
- how to interpret unavailable, blocked, failed, and completed states;
- how to propose a new Skill.

## Completion criteria

The Estate has one canonical executor-neutral Skill standard, schema, registry, template, runbook, checklist, Grace/Helen discovery and assessment behavior, and one proven read-only Repository Health Skill. No Skill creates implicit authority, no duplicate lifecycle is introduced, and future Skills can be onboarded using a complete written package without hidden context.
