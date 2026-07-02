# Transport Adapter Evaluation v1

Status: Evaluation v1  
Owner: Alfred / Chief of Staff  
Classification: Estate Internal  
Related model: `docs/collaboration/Communication_Bus_v1_Operational_Flow.md`

## 1. Purpose

This document evaluates candidate transport adapters for Estate communication while preserving the Communication Bus as the institutional messaging model.

The evaluation responds to operational friction with GitHub as a live transport, the current inability to directly observe Codex task completion, and the possibility of adopting mailbox connector patterns similar to Q Mastery / MPT-style systems.

## 2. Architectural Position

The Estate must preserve a strict distinction between the institutional messaging model and any mechanism used to move, store, notify, or surface messages.

- **Communication Bus** means the institutional messaging model: canonical envelopes, addressing, routing, acknowledgement, reply threading, work package lifecycle, review routing, promotion requests, completion reporting, audit traceability, escalation, and boundary review.
- **Transport Adapter** means a replaceable mechanism used to move, persist, notify about, or surface Communication Bus messages.

No evaluated transport replaces the Communication Bus. GitHub, local files, email, Gotify, mailbox connectors, and any future Codex status API are implementation mechanisms only. They may carry or expose bus messages, but they do not own message semantics, privacy classification, authority, routing policy, review policy, or institutional state.

## 3. Existing Repository Anchors

The current evaluation assumes these repository paths and artifacts are real anchors for v1 planning:

- `collaboration/messages/` — repository-local message lifecycle surface.
- `collaboration/mailboxes/` — mailbox directories and mailbox index.
- `collaboration/work_packages/` — work package lifecycle surface.
- `collaboration/work_packages/completions/` — machine-readable completion signals used by current Codex work packages.
- `collaboration/templates/message_envelope_v1.json` — canonical message envelope template.
- `docs/collaboration/Communication_Bus_v1_Operational_Flow.md` — Communication Bus operational model.
- `docs/collaboration/adapters/GitHub_Transport_Adapter_v1.md` — current GitHub adapter statement.
- `docs/collaboration/adapters/Local_Filesystem_Transport_Adapter_v1.md` — current local filesystem adapter statement.
- `operations/boards/parking_lot.md` — existing parking lot surface for deferred ideas.

## 4. Evaluation Criteria

Each candidate is evaluated against these criteria:

1. Local-first compatibility.
2. Ability to preserve structured messages.
3. Auditability.
4. Worker accessibility.
5. Steward approval friction.
6. Ability to support autonomous operation.
7. Ability to support completion/status detection.
8. Security and credential implications.
9. Cost and dependency profile.
10. Suitability for v1, v2, or future use.

## 5. Candidate Evaluations

### 5.1 GitHub Repository Files

**Description:** Use repository files, commits, pull requests, and future GitHub issues or boards to store or surface promoted Communication Bus messages and institutional documents.

| Criterion | Assessment |
|---|---|
| Local-first compatibility | Moderate. Git workflows can be local-first until push, but shared visibility depends on remote synchronization. |
| Structured messages | Strong when messages remain JSON or Markdown with canonical envelope metadata. |
| Auditability | Strong. Git history, diffs, commits, and pull requests provide durable audit trails. |
| Worker accessibility | Strong for Codex and developer agents with repository access; weaker for non-Git workers. |
| Steward approval friction | Moderate to high. Promotion, branch, commit, push, and PR review create deliberate friction that is good for institutional state but poor for live dispatch. |
| Autonomous operation | Moderate. Agents can write files and commits, but remote push, PR state, merge authority, and conflict resolution add operational complexity. |
| Completion/status detection | Moderate. Completion files can be observed after commit or workspace inspection, but GitHub does not inherently reveal live Codex task state. |
| Security/credentials | Requires repository credentials for remote operations. Risk is manageable but must stay behind boundary and promotion rules. |
| Cost/dependency | Low direct cost; external platform dependency. |
| Suitability | Best for v1 promoted institutional record, reviewable state, and shared documents. Not ideal as the only live transport. |

**Evaluation:** GitHub should remain the durable promoted-state and review transport. It should not be treated as the live Communication Bus itself and should not be the sole mechanism for urgent status, local worker dispatch, or private pre-promotion work.

### 5.2 Local Filesystem / Local Broker

**Description:** Use local directories, file watchers, SQLite, local queues, IPC, or a lightweight local broker to move and observe Communication Bus messages before promotion.

| Criterion | Assessment |
|---|---|
| Local-first compatibility | Strong. This is the natural local-first foundation. |
| Structured messages | Strong. JSON envelopes and Markdown payloads can be preserved exactly. |
| Auditability | Moderate to strong. Filesystem state is inspectable; append-only logs or SQLite would improve durability. |
| Worker accessibility | Strong for local Codex, scripts, Ollama/4090 workers, and local automation; weaker for remote participants without synchronization. |
| Steward approval friction | Low for local operation; appropriate because local-only movement should not imply promotion. |
| Autonomous operation | Strong. Watchers, queues, and CLI tooling can operate without external services. |
| Completion/status detection | Strong when workers emit completion files, status records, or queue acknowledgements. |
| Security/credentials | Low external credential risk; local filesystem permissions and data classification still matter. |
| Cost/dependency | Low. Can start with repository/runtime files and later add SQLite or a broker. |
| Suitability | Best near-term live/local transport priority for v1/v2 operational automation. |

**Evaluation:** A local filesystem/local broker adapter is the strongest near-term answer for local-first autonomous operation and completion detection. It should carry canonical Communication Bus messages without becoming the model itself.

### 5.3 Gmail / Email Adapter

**Description:** Use email as a transport for human-visible notifications, approvals, inbound messages, or summaries.

| Criterion | Assessment |
|---|---|
| Local-first compatibility | Weak to moderate. Email is external and account-centered, though local mail clients or export pipelines can cache messages. |
| Structured messages | Moderate. Structured JSON can be attached or embedded, but email clients often encourage lossy human text workflows. |
| Auditability | Moderate. Email has timestamps and headers, but thread state, edits, and institutional retention depend on provider and policy. |
| Worker accessibility | Moderate. Many systems can send email; safe reading and parsing require credentials and careful filtering. |
| Steward approval friction | Low for notification, but high-risk if approvals become informal replies rather than bus-governed records. |
| Autonomous operation | Moderate. Polling and SMTP/IMAP can work, but credentials, rate limits, spam controls, and provider policy are material constraints. |
| Completion/status detection | Weak to moderate. Useful for human acknowledgement, not reliable as primary machine status detection. |
| Security/credentials | High. Requires account credentials, OAuth, retention decisions, and boundary controls. |
| Cost/dependency | Usually low direct cost but dependent on external provider and account lifecycle. |
| Suitability | Future or limited v2 notification/ingress adapter after boundary rules mature. Not recommended as v1 core live transport. |

**Evaluation:** Email should be treated as a notification or human ingress/egress adapter, not an institutional source of truth. Any Gmail adapter must preserve canonical bus records locally and avoid making email replies authoritative unless converted into validated Communication Bus messages.

### 5.4 Gotify Notification Adapter

**Description:** Use Gotify or a similar self-hosted push notification service to notify operators or workers that bus events require attention.

| Criterion | Assessment |
|---|---|
| Local-first compatibility | Strong if self-hosted locally or on Estate-controlled infrastructure; moderate if exposed externally. |
| Structured messages | Moderate. Gotify can carry concise structured payloads or links, but should not carry complete institutional records by default. |
| Auditability | Moderate. Notification history exists, but it is not a substitute for repository/local bus logs. |
| Worker accessibility | Strong for human/mobile notification and scripts; less suitable as a general worker mailbox. |
| Steward approval friction | Low. Good for surfacing events without requiring GitHub checks. |
| Autonomous operation | Moderate to strong. Local automation can trigger notifications when messages arrive, stall, complete, or require approval. |
| Completion/status detection | Indirect. Gotify can report detected status changes but should not be the detector or canonical completion store. |
| Security/credentials | Moderate. Requires server URL and tokens; payload minimization is important. |
| Cost/dependency | Low if self-hosted; operational dependency on the Gotify service. |
| Suitability | Good v2 notification adapter after local status detection is reliable. Possible v1 adjunct only for notifications, not message storage. |

**Evaluation:** Gotify is a strong notification surface but a poor primary transport for full Communication Bus semantics. It should carry event summaries, links, and urgency markers while canonical records remain local/Git-backed.

### 5.5 Q Mastery / MPT-Style Mailbox Connector Pattern

**Description:** Use explicit mailboxes, inbox/outbox folders, message claiming, acknowledgement, synchronization duties, and connector processes to bridge participants or runtimes.

| Criterion | Assessment |
|---|---|
| Local-first compatibility | Strong. Mailbox folders and connector loops map naturally onto local-first operation. |
| Structured messages | Strong. Canonical envelopes, reply threading, acknowledgements, and status records can be preserved. |
| Auditability | Strong if messages are append-only or lifecycle movements are logged. |
| Worker accessibility | Strong. Different workers can consume mailbox folders or connector APIs without needing direct knowledge of every transport. |
| Steward approval friction | Low to moderate. Routine local routing can be low-friction while promotions still require approval. |
| Autonomous operation | Strong. Connector loops can synchronize mailboxes, detect stale items, emit acknowledgements, and route status. |
| Completion/status detection | Strong when completion signals are standardized as mailbox messages or completion artifacts. |
| Security/credentials | Low locally; external connectors inherit the credential risks of whatever transport they bridge. |
| Cost/dependency | Low for local folders; moderate if connector framework becomes complex. |
| Suitability | Strong v1/v2 pattern for institutional routing, especially when kept adapter-neutral. |

**Evaluation:** The mailbox connector pattern is the best conceptual bridge between the Communication Bus model and multiple transports. It should be developed as an adapter-neutral connector pattern rather than as a replacement governance layer.

### 5.6 Future Codex Task Status Adapter

**Description:** If Codex exposes reliable API or runtime access to task lifecycle events, an adapter could observe task started/running/blocked/completed/failed state and convert those events into Communication Bus status messages.

| Criterion | Assessment |
|---|---|
| Local-first compatibility | Unknown. Depends on API availability and whether local runtime events are exposed. |
| Structured messages | Potentially strong if API responses can be mapped into canonical status messages. |
| Auditability | Potentially strong if raw events are captured and normalized into repository/local records. |
| Worker accessibility | Strong for Codex-specific operations; narrow for non-Codex workers. |
| Steward approval friction | Low for status observation; no approval should be implied by task state. |
| Autonomous operation | Potentially strong because it would reduce manual completion polling. |
| Completion/status detection | Potentially very strong. This is the primary reason to revisit the adapter. |
| Security/credentials | Unknown to high. API tokens, workspace scope, and task visibility would require careful controls. |
| Cost/dependency | Unknown external dependency on Codex product/API availability and terms. |
| Suitability | Future-only until official or otherwise approved API access exists. |

**Evaluation:** A Codex task status adapter should be parked as future work. It should only translate observed Codex lifecycle events into Communication Bus status messages. It must not become the authority for completion acceptance, merge approval, review status, or institutional truth.

## 6. Recommendation Matrix

| Adapter | v1 role | v2 role | Future role | Overall recommendation |
|---|---|---|---|---|
| GitHub repository files | Promoted institutional record, reviewable documentation, PR/commit audit trail | Expanded review surfaces through issues, PR metadata, actions, or boards if useful | Long-term shared archival/review transport | Keep, but do not use as sole live transport. |
| Local filesystem / local broker | Primary local-first live transport and completion artifact surface | Add watchers, SQLite, queue semantics, or broker if patterns stabilize | Durable local substrate for autonomous operation | Prioritize near-term. |
| Gmail/email adapter | Avoid as core; possible manual notification only | Controlled notification or inbound human message adapter after boundary design | External human communication bridge | Defer until credential and boundary controls mature. |
| Gotify notification adapter | Optional notification adjunct only if no credentials are added in this package | Event notification layer over local detection | Operator alerting fabric | Prioritize after local status detection, not before. |
| Q Mastery / MPT-style mailbox connector | Use pattern concepts with existing `collaboration/mailboxes/` and canonical envelopes | Formalize connector loops, sync duties, and mailbox-aware routing | Cross-transport connector framework | Prioritize as design pattern and adapter-neutral connector model. |
| Future Codex task status adapter | Not available / do not implement | Investigate only if official access emerges | Direct task lifecycle observation | Park as future work. |

## 7. Near-Term Transport Priorities

1. **Keep the Communication Bus model stable.** All adapters must preserve canonical envelopes, message lifecycle, acknowledgement/reply semantics, review routing, promotion boundaries, and completion reporting.
2. **Prioritize local filesystem/local broker behavior.** The next operational improvement should be better local detection of inbox, claimed, in-progress, review, completed, and completion-file state.
3. **Use the mailbox connector pattern as the adapter-neutral bridge.** The existing mailbox structure should remain the conceptual interface between workers and transports.
4. **Keep GitHub as promoted institutional state.** GitHub remains valuable for auditability, shared review, and durable documentation, but it should not be overloaded as the real-time bus.
5. **Add notifications only after local status events are trustworthy.** Gotify and email are useful surfaces once local event generation is reliable.
6. **Park Codex API/task status integration.** Revisit only when official or approved task lifecycle access exists.

## 8. Future-Work Note

Future work should define a **Codex Task Status Transport Adapter** if official or approved Codex task lifecycle access becomes available. That work should map observed task events into Communication Bus status messages and completion artifacts, with explicit limits: the adapter observes and reports state; it does not grant merge authority, review approval, promotion approval, or institutional truth.

This note satisfies the current parking-lot need without editing `operations/boards/parking_lot.md` in this package.

## 9. Non-Implementation Statement

This package evaluates transport options only. It does not implement transports, add credentials, call external services, create governance, or change the Communication Bus architecture.
