# PL-0038 — Comms8 Conversation Affinity and Managed Rotation

Status: Captured
Priority: High
Category: Estate Communications / Reasoning Continuity
Originator: Pat / Steward
Date Captured: 2026-08-06
Target Milestone: After current Comms8 acceptance and stabilization work is complete

## Idea

Add governed conversation affinity and managed conversation rotation to the Estate's ChatGPT-facing Comms8 workflow.

Comms8 requests should not require one new ChatGPT conversation per request, and the Estate should not reuse one conversation indefinitely. Requests belonging to the same project or topic should normally continue in the corresponding ChatGPT reasoning thread while that thread remains useful and healthy. When a thread becomes too old, too large, degraded, or operationally unreliable, the Estate should create a successor conversation and carry forward a bounded project handoff.

The Estate, rather than ChatGPT or a browser script, should remain authoritative for selecting whether a request starts, continues, recovers, or rotates a conversation.

## Problem

Conversation history can reduce repeated context-loading costs and improve continuity across related requests. For example, updates for Project 5 should generally return to the active Project 5 conversation, while Project 7 should retain its own separate thread and a first request for Project 9 may require a new conversation.

However, long-running conversations eventually lose earlier context as the effective context window shifts. They can also accumulate stale composer state, stream errors, broken app selection, UI residue, or unrelated topic history. Reusing a single conversation forever therefore creates both reasoning and browser-reliability risks.

The current Comms8 acceptance work should not be expanded to solve this now.

## Desired Capability

Investigate a small Estate-level conversation-routing capability that can resolve a Comms8 request into one of these outcomes:

- `START_NEW_CONVERSATION`
- `CONTINUE_CONVERSATION`
- `RECOVER_CONVERSATION`
- `ROTATE_CONVERSATION`

Potential request or routing metadata includes:

- stable `topic_id` or project identifier;
- conversation policy such as `auto`, `new`, `continue_preferred`, or `continue_required`;
- active conversation ID or URL;
- conversation generation;
- approximate turn count;
- created and last-used timestamps;
- app identity;
- last successful MCP invocation;
- health state;
- maximum turn or age threshold;
- predecessor and successor conversation references;
- retirement or rotation reason;
- bounded continuation summary.

A possible default policy is to continue a healthy project conversation until a configurable threshold—such as approximately 100 turns, elapsed age, topic divergence, or health degradation—then start a successor thread for the same topic.

## Architectural Boundary

Comms8 request lifecycle remains authoritative and independent:

`created → claimed → acknowledged → responded → resolved`

ChatGPT conversation history is a reusable reasoning workspace, not authoritative Estate state.

The Estate should decide conversation affinity before browser submission. ChatGPT should not choose which project history it inherits. Browser automation should receive either an exact governed conversation target or an instruction to create a successor conversation.

Before introducing a new registry or subsystem, determine whether an existing Estate project/workflow identity, Discovery capability, communications record, or operations runtime can absorb this metadata and decision responsibility.

## Rotation and Handoff

When rotating a topic to a successor conversation, do not blindly replay the complete old transcript. Create a bounded continuation handoff containing, as appropriate:

- topic/project identity;
- current objective;
- accepted decisions;
- current authoritative state;
- unresolved questions;
- relevant artifact and receipt references;
- explicit constraints and prohibited assumptions;
- predecessor conversation reference.

The old conversation should remain historical and discoverable but no longer active for new requests unless explicitly recovered.

## Why It Is Parked

The current priority is completing the existing Comms8 Blue3 acceptance and startup stabilization. Conversation affinity and rotation are valuable but not required to prove the present request lifecycle. Adding them now would introduce scope creep across request schemas, browser routing, project identity, continuity summaries, and operational policy.

## Promotion Condition

Promote when:

1. The current Comms8 candidate acceptance and startup work is stable.
2. Multiple Estate projects regularly use ChatGPT reasoning through Comms8.
3. Repeated context reloads, cross-project contamination, very long chats, or stale-chat recovery become measurable operational costs.
4. A bounded design can reuse existing Estate project/workflow identity and communications infrastructure rather than creating unnecessary parallel institutions.
5. The Steward intentionally authorizes a focused conversation-affinity and rotation work package.

The first promoted slice should support only a minimal topic-to-active-conversation mapping, governed continue/new/rotate decisions, one bounded rotation threshold, and a continuation summary. It should not redesign Comms8 broadly.

## Explicit Non-Action

Do not modify the current Comms8 acceptance run, request lifecycle, Blue3 app, MCP tool contract, browser sender, queue ordering, or project schemas merely because this item has been captured.

Do not force a new conversation for every request.

Do not reuse one conversation forever.

Do not create a new registry, office, department, or general memory platform unless existing Estate subsystems cannot absorb the responsibility.

## Related Context

- Current Estate Comms8 Blue3 acceptance and browser automation work.
- Existing distinction between authoritative Comms8 request state and non-authoritative ChatGPT conversation context.
- Current operational lesson: both recovery of a relevant existing conversation and creation of a clean successor conversation must be supported.
