# ESTATE-HELP-001 — Steward Help and Current Capabilities Surface

Status: Pending
Owner: Office of the Steward with Grace and Helen
Execution class: discovery, explanation, generated help, bounded operator interface

## Objective

Create a current, trustworthy Steward-facing help surface that answers ordinary questions such as:

- Grace, what can we do?
- Grace, help.
- Grace, show my commands.
- What can Engineering do right now?
- Can we transcribe audio?
- Which Skills are available?
- What can I ask the Historian or Legal Expert to do?
- What is operational, unavailable, blocked, or only planned?

The answer must be generated from canonical Estate sources and current evidence rather than maintained as an independent cheat sheet that can silently become stale.

## Source-of-truth requirements

The surface must reconcile, without replacing:

- capability registry/source;
- provider catalog;
- resident capability manifests;
- Skill registry once available;
- operational baselines;
- current Helen qualification, availability, capacity, health, authorization, and freshness evidence;
- PTM/readiness where relevant;
- institutional acceptance records;
- active enabling projects and known limitations.

When sources conflict, the surface must fail closed or show the conflict. It must not infer that installed software, a catalog entry, a passing test, or historical operational status means currently dispatchable.

## Required outputs

Provide three complementary views:

1. Conversational help through Grace and Helen.
2. Human-readable Steward Cheat Sheet generated from canonical state.
3. Machine-readable current-capabilities snapshot with source references and generated timestamp.

The generated cheat sheet may be committed only when appropriate as a dated snapshot; the live conversational answer must use current state.

## Information model

For each resident, department, capability, and Skill, provide as applicable:

- plain-English name and short description;
- formal ID/version;
- owner;
- maturity level;
- current availability;
- current dispatchability;
- qualified providers/workers;
- accepted operational scope;
- prohibited or unsupported scope;
- classification ceiling;
- required authority and approvals;
- whether proposal-only or direct governed execution is possible;
- common phrases the Steward can say;
- expected outputs;
- likely failure/block reasons;
- enabling project when unavailable;
- institutional acceptance separately;
- source references and freshness.

Do not show secret values, credentials, raw tokens, sensitive prompts, or unrestricted internal paths in ordinary help output.

## Conversational behavior

Grace must recognize at minimum:

- help
- what can we do
- show my commands
- current capabilities
- what can Engineering do
- what can <resident> do
- can we <outcome>
- how do I ask for <outcome>
- what Skills are available

Grace should answer in plain language first, then offer bounded detail. It must distinguish:

- operational now;
- available but requires authorization;
- registered but not operational;
- temporarily unavailable;
- capability gap;
- prohibited;
- institutionally accepted or not.

Grace must not execute merely because the Steward asked what is possible.

Helen must support questions such as:

- do we have this capability;
- who is qualified to do it;
- is it available now;
- what evidence is stale;
- what enabling project is required;
- why is it not dispatchable.

## Steward phrasing guide

For every operational item, generate memorable examples in patterns such as:

- Grace, ask Engineering to draft...
- Grace, ask Engineering to review these exact files...
- Grace, prepare a proposal before execution.
- Grace, proceed through the governed process without widening scope.
- Helen, do we have a governed transcription capability?
- Grace, use the Check Git Skill and report only.

Include aliases and short phrases while preserving formal identities behind the scenes.

## Scope and authority guardrails

- Help is read-only and cannot create authority.
- A help request cannot trigger provider execution, repository mutation, merge, purchase, deletion, acceptance, or external communication.
- Suggested commands must include scope and authorization guidance when the task is sensitive.
- The surface must never claim a capability based only on local installation.
- Historical success must not be presented as current availability without fresh evidence.
- Institutional acceptance must never be inferred.

## Initial canonical snapshot

Generate an initial Estate help snapshot covering at least:

- Grace;
- Helen;
- Engineering;
- qwen.local.text;
- codex.execution.cli;
- current registered but not necessarily live providers such as ComfyUI;
- capability onboarding framework;
- Skills framework status;
- Whisper and Qwen Coder status as actually supported by evidence;
- WebUI/Gateway operational path and current limitations;
- current institutional acceptance state.

Do not hard-code an unsupported statement. If the repository cannot prove current availability, show unknown or unavailable with the reason.

## Interface options

Implement the smallest canonical surfaces supported by the existing architecture, potentially including:

- Grace natural-language intent/route;
- Helen capability inquiry route;
- Estate CLI command such as `estate help`, `estate capabilities`, or the repository's established naming style;
- generated Markdown/JSON artifacts;
- optional Web UI help action only if it reuses existing integration surfaces.

Do not create an unrelated standalone dashboard or duplicate registry.

## Freshness and caching

- Every response/snapshot records generation time and source digests or references.
- Cache only when bounded and invalidate on relevant registry/evidence changes or expiry.
- If fresh evidence cannot be obtained, label the answer accordingly.
- Current availability should be recomputed or verified rather than copied indefinitely from a dated report.

## Testing

Include:

- natural-language intent tests;
- alias and ambiguous-request tests;
- resident-scoped and department-scoped help tests;
- operational/registered/unavailable/gap/prohibited distinctions;
- stale evidence and conflicting-source tests;
- no-execution-on-help tests;
- secret-redaction tests;
- institutional-acceptance separation tests;
- source-reference and freshness tests;
- generated Markdown and JSON validation;
- Web UI/Grace operator acceptance using ordinary phrases.

## Deliverables

- docs/architecture/Estate_Steward_Help_and_Capability_Discovery.md
- docs/operations/Estate_Steward_Help_Runbook.md
- generated current-capabilities JSON schema and implementation
- generated Steward Cheat Sheet
- Grace/Helen integration changes
- tests and acceptance evidence
- implementation/closure report

## Completion criteria

The Steward can ask Grace or Helen ordinary questions about what the Estate, a resident, a department, a capability, or a Skill can currently do and receive a clear, current, source-grounded answer with memorable request examples, scope and authority limits, unavailable/gap explanations, and institutional acceptance stated separately. The help request itself remains strictly read-only and cannot silently execute work.
