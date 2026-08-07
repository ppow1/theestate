# Estate Grace Operational Reasoning and Action Architecture

Status: Current architecture checkpoint  
Classification: Estate Internal  
Date: 2026-08-07

## Purpose

This document records the current architectural model for Grace's operational reasoning and action loop after the 2026-08-07 Comms8, durable consultation, CME, reasoning-resident, execution-provider, evidence-acquisition, and escalation acceptance work.

It is intentionally a stable architectural explanation rather than a chronological repair log. Historical review receipts remain the evidence trail for how the architecture was reached.

## Core Principle

**Grace reasons over Estate state; Grace does not own Estate state.**

Grace is the Estate's Operations resident. Her responsibility is to understand work, priorities, dependencies, resources, deadlines, blockers, and momentum and then keep work moving through governed mechanisms. She should not be required to remember the Estate in model context.

The durable Estate is the memory. Grace queries it, reasons over a bounded working set, and causes governed state transitions.

## Grace's Institutional Role

Grace is the first resident being used to prove resident-specific operational logic, but she is not merely a generic resident test fixture.

Grace has an unusually broad operational role:

- maintain visibility across active work;
- use the Continuous Momentum Engine (CME) to keep eligible work moving;
- create and continue reasoning consultations;
- obtain outside reasoning when needed;
- route justified action through provider-neutral execution mechanisms;
- observe evidence and decide what should happen next;
- detect stalls and blockers;
- escalate bounded unresolved decisions to the Steward;
- eventually reason across multiple concurrent resident and project lanes.

Other named residents will have specialized logic suited to their roles. They should publish durable work state that Grace can inspect rather than requiring Grace to hold their state in conversational memory.

## The Durable Reasoning Model

The canonical local consultation store is SQLite-backed. The accepted data location is:

`A:\theestate-data\consultations\consultations.db`

The consultation store separates logical reasoning identity from transport and execution mechanics.

A logical reasoning root uses a stable numbered identity such as:

- `5.00` — root consultation;
- `5.01` — first reasoning continuation;
- `5.21` — twenty-first continuation;
- `.99` — final continuation before explicit rollover into a new root under the accepted lineage rules.

The decimal suffix therefore provides both lineage and a simple observable measure of reasoning cycles. It must not be confused with transport retries or execution attempts.

Durable consultation history can preserve, as applicable:

- objective/question;
- reasoning responses;
- structured decisions;
- validation state;
- continuation lineage;
- Comms8 transport attempts;
- execution requests and physical attempts;
- execution evidence;
- evidence-acquisition history;
- PTM/project references;
- tags/search metadata;
- escalation records;
- Steward decisions and Steward-supplied evidence;
- post-decision outcomes;
- projection state.

The working context presented to a resident or reasoning provider is a bounded projection from this durable state. A physical chat is disposable.

## Authority Boundaries

### SQLite consultation state

SQLite is the durable logical reasoning record. It preserves what question was being answered, what evidence existed, what decisions were made, what continuations occurred, and what downstream work resulted.

### Estate Comms8

Comms8 is the governed communication/lifecycle transport. It is not the consultation memory system.

A logical turn may require more than one physical Comms8 transport attempt. For example, a transport may expire and be replaced while the logical consultation identity remains unchanged.

The expected relationship is:

`durable consultation state -> Comms8 request -> reasoning/worker lifecycle -> authoritative Comms8 result -> durable consultation update`

### GitHub

GitHub is a durable human-readable projection/archive where applicable. It is non-authoritative and must remain non-blocking. GitHub unavailability must not prevent local consultation reasoning or lifecycle progression.

### Physical ChatGPT/Open WebUI conversations

Physical conversations are execution surfaces, not institutional memory. If a conversation is replaced, the reasoning chain must be reconstructable from durable Estate state.

## Structured Reasoning Decisions

The accepted reasoning decision boundary distinguishes at least:

- `INFORMATION_ONLY`
- `EXECUTION_RECOMMENDED`
- `MORE_REASONING_REQUIRED`
- `STEWARD_DECISION_REQUIRED`

Execution authority is not inferred from prose.

A valid `EXECUTION_RECOMMENDED` result carries a complete provider-neutral execution specification, including the accepted equivalents of:

- objective;
- required capability;
- allowed scope;
- prohibited scope;
- evidence requirements;
- validation criteria;
- consultation correlation.

Malformed recommendations fail closed and can generate bounded reasoning-format repair continuations; the execution validator is not weakened to make an incomplete recommendation pass.

## Provider-Neutral Action

Execution is modeled as a logical execution request plus one or more physical attempts.

The consultation/orchestration layer requests a capability. It does not hard-code Codex as the institution.

An eligible provider may currently be `codex-cli-openai`, but provider-specific translation belongs inside the provider adapter. The surrounding reasoning and CME architecture should remain usable with other local or remote providers.

This distinction permits future provider capacity management and parallel execution without changing consultation semantics.

## Evidence Before and After Action

The reasoning loop intentionally allows evidence acquisition before execution.

A valid sequence may be:

`reason -> request evidence -> acquire evidence -> reason -> decide no action`

or:

`reason -> request evidence -> acquire evidence -> reason -> recommend action -> execute -> observe -> reason again`

`MORE_REASONING_REQUIRED` is distinct from `EXECUTION_RECOMMENDED`. Evidence acquisition exists to reduce uncertainty; it is not itself the engineering recommendation.

The accepted autonomous evidence path is local-history-first. Provider-neutral read-only acquisition is used only when durable existing evidence does not satisfy the request. Provider acquisition is bounded; the current accepted root-level evidence-acquisition limit is three.

## Escalation as an Instrumented Safety Valve

When autonomy reaches a bounded uncertainty or authority limit, Grace does not fabricate closure.

The consultation can enter `STEWARD_DECISION_REQUIRED` and persist an instrumented escalation record containing a decision-time snapshot of:

- known facts and evidence-backed confidence;
- working interpretations and confidence;
- explicit unknowns and their impact;
- options where real;
- action-confidence estimates;
- the current recommendation when one can responsibly be made;
- what additional evidence or authority would materially increase confidence.

The Steward decision is stored separately from the immutable escalation snapshot. Steward-supplied new evidence is separately identifiable. The post-decision observed outcome is also separately correlated.

This creates a future decision-learning corpus without automatically expanding autonomous authority.

## Continuous Momentum Engine

CME is the operational owner that observes durable eligibility and wakes the appropriate bounded worker. It is not a substitute memory system.

For the ChatGPT reasoning resident, the accepted ownership model is:

- reasoning work becomes eligible in durable state;
- CME detects eligibility;
- CME launches the canonical bounded ChatGPT mailbox worker;
- the worker uses generic mailbox semantics rather than a Steward-supplied request ID;
- authoritative Comms8 lifecycle completion is required;
- CME reconciles to truthful idle/completed state;
- duplicate ticks are inert;
- stale ownership can be recovered safely when recorded owners are dead and no authoritative active lease prevents recovery.

Browser/model text such as `WORKER_COMPLETE` is not authoritative lifecycle truth. Late Comms8 completion must be reconciled from authoritative state.

## The Proven Single-Lane Loop

As of this checkpoint, the following controlled loop has been proven:

1. Grace receives ordinary intent.
2. A durable consultation is created.
3. CME detects reasoning eligibility.
4. ChatGPT is woken as the reasoning resident.
5. ChatGPT may request bounded evidence.
6. Evidence is acquired and persisted.
7. CME wakes ChatGPT again.
8. ChatGPT can return a validated `EXECUTION_RECOMMENDED` specification.
9. One provider-neutral logical execution request is created.
10. Capability routing selects an eligible execution provider.
11. The provider performs a bounded physical attempt.
12. Execution evidence and validation are persisted.
13. The resulting reasoning continuation becomes eligible.
14. CME wakes ChatGPT again.
15. ChatGPT reevaluates the actual execution evidence.
16. Grace receives the authoritative current outcome.
17. CME returns to `IDLE`; duplicate activation is suppressed.

The controlled-fixture acceptance used exactly one logical execution request and one physical provider attempt, changed only the approved fixture, validated the correction, and then returned an authoritative `INFORMATION_ONLY` reevaluation.

## What Is Proven Versus What Is Future Work

### Proven

- durable consultation memory;
- numbered root/continuation lineage;
- transport-attempt separation;
- provider-neutral execution requests and attempts;
- durable execution/evidence history;
- bounded evidence acquisition;
- structured reasoning decisions;
- CME-owned ChatGPT reasoning activation;
- browser completion reliability with authoritative reconciliation;
- stale-owner recovery and duplicate suppression;
- instrumented Steward escalation;
- non-blocking GitHub projection;
- one complete autonomous reason/evidence/execute/observe/reason loop.

### Deliberate future extensions

- multiple concurrently active consultation lanes;
- provider capacity and scheduling across multiple seats/providers;
- Estate-wide resident-neutral work-state contract;
- Grace portfolio querying across all residents/projects;
- dependency/deadline/resource-aware prioritization;
- common stall/heartbeat/momentum semantics for residents;
- analytics across reasoning-cycle counts, escalations, decisions, and outcomes;
- learning from escalation history without automatic authority expansion;
- Grace character/personality restoration and conversational voice after functional competence is stable;
- Estate-wide troubleshooting cookbook and diagnostic tooling.

## Parallelism Hook

Current acceptance is intentionally single-lane. New code should avoid creating new assumptions that there is only one globally current consultation, worker, activation, or execution.

Future parallel operation should be able to query durable state resembling:

- root A waiting on reasoning;
- root B executing;
- root C waiting on Steward;
- root D acquiring evidence;
- root E ready for continuation.

Grace should query that portfolio rather than track it in model memory.

The consultation root/continuation identity remains the semantic lane. Scheduling and provider capacity are separate concerns.

## Character Versus Function

Grace's current priority is functional competence: she must be able to understand intent, query durable state, reason, route work, observe evidence, preserve momentum, and escalate truthfully.

Grace's voice, vocabulary, conversational style, initiative style, disagreement behavior, and broader Character Architecture remain important but are a later layer. Functional and character development should remain separable so behavioral faults are diagnosable.

## Architectural Summary

The Estate is moving from conversation-as-memory toward durable reasoning-as-state.

Context windows become working sets rather than knowledge bases. Drift becomes detectable because questions, evidence, decisions, actions, and continuations survive outside the chat that produced them.

Grace's job is not to remember the kingdom.

Grace's job is to understand the kingdom's durable state and keep it moving.