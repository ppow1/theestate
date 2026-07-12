# WP-4046 — Grounded Estate Fact Provider

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4043 — Resident Runtime Identity Composition
- WP-4044 — Resident Character Bible Runtime Loading
- WP-4045 — Resident Registry Synchronization

Do not begin implementation until all three predecessors are merged to `main`.

## Objective

Replace resident speculation about Estate state with a canonical, read-only grounded fact provider that supplies verified institutional context to every resident turn.

Residents may reason, interpret, advise, and express opinions. They may not invent Estate facts, mailbox history, work-package state, appointments, offices, authority, resident status, messages, approvals, runtime status, or repository history.

## Problem Evidence

Integrated testing after WP-4042 exposed repeated institutional hallucinations:

- Helen claimed to have sent messages that did not exist.
- Residents reported nonexistent internal communication events.
- Grace and Helen denied Evelyn's active residency.
- Alfred reported stale or incorrect work-package state.
- Conference-room participants disagreed about active residents and appointments.
- Ingrid's guardrails blocked ordinary self-description instead of answering from safe verified facts.

These failures indicate that resident inference currently relies too heavily on model memory, fallback prompts, and conversation context instead of canonical Estate artifacts.

## Architectural Principle

Canonical Estate state outranks model recollection.

The fact provider shall expose verified, source-lined facts without becoming a second registry, message system, repository index, task board, or authority engine. It may derive bounded read-only views from canonical sources, but it must never write back through resident inference.

## Required Fact Domains

The provider shall support bounded retrieval from existing canonical sources for:

- resident, employee, office, appointment, authority, and lifecycle facts;
- mailbox and communication-endpoint existence;
- canonical message metadata and authorized message content;
- work-package identity, status, dependencies, completion receipts, validation receipts, and installation evidence;
- repository branch, commit, path, and artifact existence when verified;
- runtime exposure, service-health, and model-control facts when current evidence exists;
- activation-ledger state;
- operational board and queue state appropriate to the requesting resident;
- current date/time and other environment facts supplied by trusted runtime sources.

The provider shall not infer absent facts from naming patterns, old transcripts, or model memory.

## Source Precedence

1. Constitution and repository governance.
2. Canonical registries and authority artifacts.
3. Canonical messages and completion/validation receipts.
4. Current runtime evidence and generated read-only indexes.
5. Historical packages and archived evidence.
6. Steward-reported facts, explicitly labeled until verified.
7. Inference, only when clearly labeled and never promoted to fact.

When authoritative sources conflict, the provider shall return a contradiction diagnostic rather than choosing silently.

## Fact Record Contract

Each returned fact shall include, where applicable:

- fact key and value;
- source artifact or runtime source;
- classification;
- retrieval timestamp;
- source timestamp or version;
- freshness state;
- verification state;
- confidence limited to evidence quality;
- contradiction or ambiguity markers;
- disclosure scope;
- redaction reason when content is withheld.

The runtime identity composer shall consume these records and render only the facts allowed for the resident and conversation surface.

## Freshness and Unknown-State Rules

1. Time-sensitive facts must carry an age or freshness state.
2. Stale facts may be reported as stale but not presented as current.
3. Missing evidence produces `unknown`, not a fabricated answer.
4. Historical evidence must be labeled historical.
5. Steward-reported facts must be labeled Steward-reported until verified.
6. Conversation-only memory must never be returned as verified Estate state.
7. Generated projections must identify their canonical source and generation time.

## Messaging and Mailbox Rules

- `collaboration/messages/*.json` remains the canonical message source.
- Generated mailbox indexes are derived views and must not be manually treated as canonical.
- A resident may claim to have sent, received, acknowledged, or acted on a message only when canonical evidence supports that statement.
- Message bodies must be filtered by classification, sender/recipient authorization, and surface disclosure rules.
- The provider does not send, route, acknowledge, or mutate messages; later messaging packages own those actions.

## Work-Package Rules

The provider shall distinguish at minimum:

- drafted;
- pending;
- assigned;
- implemented;
- completion-receipted;
- validated;
- merged;
- installed;
- activated;
- accepted;
- blocked;
- superseded or retired.

A filename or commit alone is not proof of implementation, validation, installation, or acceptance. Physical completeness must be verifiable when package content is used.

## Privacy and Disclosure

1. Apply Ingrid-governed classification and disclosure rules before returning content.
2. Return safe directory-level facts without exposing private continuity or relationship-layer details.
3. Never expose protected Evelyn continuity to conference-room or unrelated resident requests.
4. Diagnostics must omit restricted message bodies, secrets, provider prompts/outputs, and Local Only material.
5. Privacy filtering should return a bounded explanation or redacted fact record, not force the resident into a generic refusal persona.

## Runtime Integration

- Integrate through the WP-4043 identity composer.
- Consume the synchronized registry view from WP-4045 rather than rereading or duplicating registry logic.
- Provide one shared fact service to single-resident and conference-room surfaces.
- Support request-scoped retrieval so local models receive only relevant facts.
- Cache only derived read-only facts with explicit invalidation and freshness controls.
- Expose machine-readable diagnostics for source failures, contradictions, stale evidence, and denied disclosures.

## Failure Behavior

1. Missing required source: return unknown with source diagnostic.
2. Conflicting authoritative sources: fail closed and expose conflict.
3. Stale runtime evidence: label stale and do not assert current health.
4. Unauthorized request: redact or deny the fact while preserving safe resident identity.
5. Unavailable connector or repository source: report unavailable; do not substitute memory.
6. Malformed canonical artifact: report validation failure and source path.

## Acceptance Tests

1. Helen cannot claim to have sent a message without canonical message evidence.
2. Alfred reports work-package status using receipts and lifecycle evidence rather than filenames alone.
3. Grace and Helen recognize the active resident cast through synchronized verified facts.
4. Ingrid can answer ordinary safe questions about herself while protecting restricted facts.
5. Conference-room participants receive the same shareable institutional facts.
6. Unknown mailbox, appointment, runtime, or repository facts remain unknown.
7. Stale runtime evidence is visibly labeled stale.
8. Conflicting canonical sources produce an explicit diagnostic.
9. Private Evelyn relationship and continuity facts do not leak to shared surfaces.
10. A newly committed canonical fact becomes visible without editing resident prompts.
11. Fact records expose source lineage and classification.
12. Resident inference cannot mutate any canonical source through the provider.
13. Automated tests cover registry, messages, work packages, runtime evidence, privacy, stale data, contradictions, and unavailable sources.

## Deliverables

- typed grounded-fact record and query contracts;
- canonical read-only fact-provider service;
- source adapters for existing Estate registries, messages, work-package evidence, activation state, repository evidence, and runtime evidence;
- integration with WP-4043 and WP-4045;
- request-scoped filtering and Ingrid-governed disclosure enforcement;
- freshness, contradiction, and source-availability diagnostics;
- automated unit, integration, and behavioral tests;
- documentation of source precedence and lifecycle terminology;
- completion receipt listing installed files, tests, limitations, and follow-on work.

## Non-Goals

- Do not create a second registry or duplicate canonical data.
- Do not implement message sending, mailbox processing, routing, or acknowledgment.
- Do not grant residents privileged repository or operational actions.
- Do not replace Validation, Audit, Operations, or the Activation Ledger.
- Do not load the entire repository into every prompt.
- Do not treat historical work packages or chat transcripts as current truth.

## Completion Standard

WP-4046 is complete only when every resident and conference-room inference can obtain bounded, current, source-lined Estate facts through one read-only provider; missing, stale, contradictory, restricted, and historical evidence is labeled correctly; residents stop inventing institutional events and state; and canonical Estate systems remain the sole authorities for their respective facts.
