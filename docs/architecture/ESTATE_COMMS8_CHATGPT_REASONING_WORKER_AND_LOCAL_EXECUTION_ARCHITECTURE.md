# Estate Comms8 — ChatGPT Reasoning Worker and Local Execution Architecture

Status: Architectural record and implementation campaign narrative
Date: 2026-08-04
Owner: Office of the Steward / Estate Engineering

## Purpose

This document records the current Estate Comms8 design, why it exists, the operating sequence it is intended to support, the authority boundaries it must preserve, and the implementation path taken to reach the current candidate state.

Estate Comms8 is not merely another MCP endpoint. It is the communications and orchestration boundary that allows the Estate to use ChatGPT as a governed high-level reasoning worker while preserving Grace as the authoritative workflow controller and preserving local providers, OpenHands, Qwen-class coding models, and Codex CLI as specialist execution resources.

The design arose from a practical limitation:

- ChatGPT chat is turn-based.
- An MCP/App can expose tools during a turn, but it does not independently wake an idle chat.
- Earlier MCP work proved that ChatGPT could exchange data with an external mailbox, but repeated approval prompts made the workflow impractical.
- Browser automation had already proved capable of detecting turn completion, detecting composer availability, navigating ChatGPT, and submitting a short prompt.

The resulting design uses browser automation only to create a turn. All substantive work moves through Estate Comms8 MCP messages and artifacts.

## Core concept

The Estate does not attempt to make ChatGPT continuously reactive.

Instead, it provides an external turn engine:

```text
Grace detects or creates work
        ↓
Grace writes a structured Estate Comms8 request
        ↓
Wake worker acquires a bounded wake lease
        ↓
Browser automation opens the approved ChatGPT conversation
        ↓
Browser automation submits a fixed mailbox-processing instruction
        ↓
ChatGPT starts a normal chat turn
        ↓
ChatGPT reads, claims, acknowledges, and processes the request through MCP
        ↓
ChatGPT writes a structured response through MCP
        ↓
Grace reconciles the response and advances the workflow
```

The browser is therefore a doorbell, not a data bus.

The visible chat transcript is not the authoritative result channel. A turn succeeds only when the expected correlated response exists in Estate Comms8 and passes schema, workflow, provenance, and idempotency validation.

## Intended role of ChatGPT

ChatGPT serves as a senior reasoning checkpoint, not as the runtime controller.

Appropriate ChatGPT responsibilities include:

- interpreting an ambiguous Steward objective;
- reviewing a proposal produced by Grace;
- identifying missing constraints or architectural risks;
- reconciling conflicting reports from multiple providers;
- authoring or correcting a work package;
- deciding whether local execution is sufficient;
- preparing a bounded Codex-ready escalation package;
- reviewing difficult implementation evidence;
- issuing a final acceptance, correction, or escalation recommendation.

ChatGPT does not own:

- authoritative workflow state;
- provider registration;
- execution dispatch;
- retry authority;
- stage-transition authority;
- process supervision;
- persistent runtime truth;
- direct uncontrolled shell or repository mutation.

Grace remains authoritative for workflow progression and routing.

## Intended local execution sequence

The exact path may vary by work type, but the target operating sequence is approximately:

```text
Steward objective
    ↓
Grace captures and interprets the objective
    ↓
Grace drafts a proposal, specification, or initial work package
    ↓
ChatGPT reviews the proposal through Estate Comms8
    ↓
Grace adopts corrections and advances
    ↓
Grace dispatches bounded work to a local provider
    ├── deterministic tools
    ├── OpenHands
    ├── Qwen / Qwen3-Coder
    └── another approved local provider
    ↓
Grace runs deterministic validation and reconciliation
    ↓
ChatGPT performs higher-level evaluation when justified
    ↓
If necessary, ChatGPT prepares a Codex-ready execution package
    ↓
Grace dispatches through the existing Codex CLI adapter
    ↓
Codex performs bounded repository-aware engineering
    ↓
Grace collects results and evidence
    ↓
ChatGPT performs final reasoning review when policy requires it
    ↓
Grace closes, retries, corrects, escalates, or returns to the Steward
```

The purpose is not to use every provider on every workflow. The purpose is to use the cheapest and most local capable layer first, while preserving access to stronger reasoning and implementation resources when required.

## Provider-routing philosophy

A useful decision ladder is:

```text
LEVEL 0 — deterministic
Can a script, schema check, test, or rule decide this?
Use that.

LEVEL 1 — lightweight local reasoning
Can a small local model classify, summarize, or transform it?
Use that.

LEVEL 2 — local engineering model
Can Qwen3-Coder or another local coding model perform the bounded task?
Use that.

LEVEL 3 — ChatGPT reasoning
Does the work require planning, reconciliation, architecture, or judgment?
Wake ChatGPT.

LEVEL 4 — Codex CLI
Does the work require strong repository-aware implementation or difficult debugging?
Dispatch a prepared Codex package.

LEVEL 5 — Steward
Is the decision strategic, destructive, financially material, security-sensitive, or genuinely ambiguous?
Escalate.
```

## Estate Comms8 authority boundary

Estate Comms8 owns Estate orchestration communication, not the whole Estate.

Its responsibilities include:

- structured reasoning requests;
- workflow and stage correlation;
- message claims and leases;
- acknowledgements;
- structured replies;
- artifacts and artifact references;
- provenance;
- expiry;
- idempotency;
- typed failures;
- stale-claim recovery;
- reconciliation receipts;
- wake eligibility and wake correlation.

It does not replace:

- Grace;
- Traffic Controller;
- Execution Dispatch;
- provider catalog and health/capacity evidence;
- provider-neutral adapter interfaces;
- repository truth;
- Comms7 lifecycle authority;
- institutional validation and acceptance rules.

## Relationship to Ionoge Comms7

CueMastery’s Ionoge Comms7 implementation served as the donor architecture.

Comms7 had already proven several critical ideas:

- a public MCP endpoint could be reached from hosted AI clients;
- lane-aware mailboxes could carry durable messages;
- messages could be listed, read, acknowledged, posted, and resolved;
- a PHP-native server implementation could operate within HostVerge constraints;
- narrow typed tools were preferable to a broad generic action surface;
- server-side lifecycle authority should not be replaced by the client.

Estate Comms8 preserves those lessons but owns a different domain.

Comms7 remains authoritative for its C### and pending-record lifecycle. Estate Comms8 owns Estate reasoning-worker requests, replies, workflow correlation, artifacts, claims, leases, and reconciliation.

Traffic Controller may coordinate both systems but does not replace their lifecycle authority.

## Typed MCP surface

The candidate Estate Comms8 foundation exposes seven typed tools covering the message lifecycle:

```text
create
list
read
claim
acknowledge
respond
resolve
```

These tools are deliberately narrow.

The MCP surface does not expose arbitrary command execution, arbitrary file mutation, or a generic remote-action endpoint.

The narrow surface supports:

- lower approval risk;
- clearer auditing;
- deterministic schema validation;
- bounded authority;
- safer retries;
- easier failure classification;
- independent rollback.

## Request and response contracts

Every request is versioned and correlated.

Conceptually, a request includes:

```json
{
  "schema_version": "estate.comms8.request/v1",
  "workflow_id": "WF-...",
  "stage_id": "STAGE-...",
  "message_id": "MSG-...",
  "correlation_id": "CORR-...",
  "parent_message_id": null,
  "attempt": 1,
  "message_type": "proposal_review_request",
  "assigned_worker": "chatgpt-orchestrator",
  "status": "ready",
  "instructions": "...",
  "artifacts": [],
  "response_contract": {},
  "expires_at": null
}
```

A response is accepted only when:

- workflow and correlation identifiers match;
- sender and stage are eligible;
- the response contract validates;
- the idempotency key is valid;
- the response is not stale;
- the stage transition is permitted;
- provenance and audit requirements are satisfied.

ChatGPT may recommend a stage transition. Grace decides whether the transition is valid and authorized.

## Wake worker design

The wake worker is a bounded browser-control component.

Its responsibilities are:

- watch for an eligible wake record;
- acquire a lease;
- identify the exact approved ChatGPT conversation;
- verify composer readiness;
- submit a fixed instruction;
- observe UI state;
- wait for the authoritative MCP response;
- classify failures;
- release, retry, or dead-letter according to policy.

The worker must recognize at least:

```text
READY_TO_SUBMIT
TURN_RUNNING
TOOL_RUNNING
APPROVAL_REQUIRED
RATE_LIMITED
LOGIN_REQUIRED
NETWORK_ERROR
TURN_COMPLETE
CORRELATED_RESPONSE_RECEIVED
CORRELATED_RESPONSE_MISSING
```

The prompt submitted by the browser remains stable and contains no substantive work data. A representative instruction is:

```text
Process the next eligible request assigned to the Estate ChatGPT reasoning worker.
Read the request through Estate Comms8, follow its response contract, and write the result through Estate Comms8 before ending this turn.
```

## Approval-drip objective

A major historical failure mode was repeated tool approval.

The Estate Comms8 candidate is intentionally designed to determine whether normal mailbox reads and writes can operate under an app/session trust posture without repeated interruption.

The target behavior is:

- read and routine mailbox operations proceed without repeated prompts;
- higher-risk operations remain outside this MCP surface;
- platform safety and workspace policy remain authoritative;
- no attempt is made to bypass ChatGPT security controls.

Approval behavior must be measured in a real authenticated ChatGPT App session. The absence of an approval dialog does not prove success unless a real MCP tool invocation occurred.

## Repository and deployment topology

Before Estate Comms8 implementation, the Estate’s intended operating topology had to be implemented.

The resulting model separates:

```text
A:\theestate-common
    Normal Git source authority

A:\theestate-blue
    Non-Live candidate worktree

A:\theestate-green
    Peer non-Live candidate worktree

A:\theestate-live
    Immutable release root controlled by an active-release manifest

A:\theestate-data
    External standard operational state

A:\theestate-sensitive-data
    Reserved sensitive-data boundary

A:\theestate-backup
    Distinct recovery boundary
```

The active transitional Estate remained available throughout topology work.

Candidate services use non-canonical ports. Live activation requires a separate explicit Steward gate.

No implementation package is allowed to develop directly inside Live or promote itself.

## Four-repository engineering environment

Estate Comms8 required four local repositories:

```text
ppow1/theestate
ppow1/CueMastery
ppow1/ionoge-vps
ppow1/ionoge-site
```

Roles:

- `theestate`: primary implementation and governance repository;
- `CueMastery`: Comms7 and mailbox donor/reference;
- `ionoge-vps`: VPS, Caddy, tunnel, deployment, backup, and rehabilitation source;
- `ionoge-site`: HostVerge/PHP/MCP external-surface reference.

FAQ repositories were explicitly unrelated and excluded.

## Candidate implementation state

The Estate Comms8 candidate was built in Blue.

Candidate boundary:

```text
Source: A:\theestate-blue
State: A:\theestate-data\candidate-blue-runtime
Local MCP endpoint: http://127.0.0.1:11808/mcp
Implementation: staging/estate_comms8
```

Implemented foundation capabilities include:

- versioned request and response contracts;
- typed MCP contracts;
- atomic persistence;
- claims and leases;
- expiry;
- stale-claim recovery;
- provenance;
- audit;
- idempotency;
- typed failures;
- reconciliation receipts;
- provider-neutral reconciliation through existing Estate adapter results;
- no direct live-provider calls during candidate validation.

The candidate vertical slice proved:

```text
created
→ claimed
→ acknowledged
→ responded
→ reconciled
→ resolved
```

Duplicate-delivery and stale-worker rejection were also validated.

## Browser-worker implementation state

Package 3 added:

- wake queue and lease contracts;
- bounded retries;
- stale recovery;
- dead-lettering;
- exact-conversation protection;
- fixed-instruction-only submission;
- UI-state observation;
- MCP-correlated success validation;
- browser restart recovery;
- wrong-conversation rejection;
- wrong-workflow response rejection;
- approval-interruption handling;
- rate-limit/login failure handling;
- full candidate orchestration harnesses.

A Node/Playwright bridge reused the existing ChatGPT Conversation Archive runtime and dedicated persistent browser profile.

The candidate orchestration sequence completed in simulation with `live_provider_called=false`, preserving the candidate-only boundary.

## External reachability problem

The local Blue endpoint at `127.0.0.1:11808` is not directly reachable by ChatGPT web.

A real ChatGPT App requires an externally reachable HTTPS MCP endpoint.

The candidate external architecture became:

```text
ChatGPT App
    ↓ HTTPS
estate-comms8-blue-candidate.ionoge.com
    ↓ Caddy on DigitalOcean VPS
bounded SSH remote-loopback tunnel
    ↓
Blue Estate Comms8 at 127.0.0.1:11808
```

The design includes separate credentials for:

- ChatGPT to candidate endpoint;
- Ionoge to Blue upstream;
- Caddy to Blue.

It also includes:

- namespace-only deployment;
- backup and rollback;
- PHP validation;
- manifest uniqueness;
- fail-closed behavior;
- secret redaction;
- credential rotation and revocation;
- startup, shutdown, health, and recovery procedures.

## DNS and HostVerge work

The candidate hostname was intended to point to the DigitalOcean VPS at:

```text
64.227.21.54
```

The DNS authority was found to be StackDNS, managed through HostVerge’s StackCP control panel.

There was no documented provider API or SSH-based DNS mutation path. DNS was therefore classified as control-panel automation only.

The zone contained wildcard records:

```text
*.ionoge.com A     185.146.167.203
*.ionoge.com AAAA  2a07:7800:1::203
```

The candidate hostname initially inherited those wildcard values.

A bounded browser worker was created to protect against edits outside the exact candidate hostname. Multiple attempts to reuse the authenticated browser profile exposed several real integration problems:

- profile locking;
- authentication state not surviving a separate automation context;
- Playwright persistent-context mismatch;
- CDP attachment timeout;
- StackCP internal DNS mutation contract uncertainty;
- UI submission that did not create the record;
- direct HTTP mutation attempts that timed out.

The automation was eventually able to:

- attach through low-level CDP;
- verify the authenticated HostVerge page;
- verify the `ionoge.com` zone;
- verify wildcard records remained unchanged;
- verify no candidate exact-host record existed.

The actual candidate record was ultimately created manually in the control panel:

```text
estate-comms8-blue-candidate.ionoge.com
A
64.227.21.54
```

This was intentionally treated as a bounded operator action rather than continuing to spend engineering effort reverse-engineering a single StackCP save operation.

## Current post-DNS state

At the time of this record:

- the exact-host A record is visible in StackCP;
- authoritative DNS resolves the candidate hostname to `64.227.21.54`;
- no authoritative exact-host AAAA answer is expected;
- some recursive resolvers may temporarily retain the previous wildcard answer until TTL expiration;
- Blue candidate service, tunnel, and Caddy restoration are in progress;
- the transitional Estate remains active on ports `8766`, `11435`, and `8080`;
- Estate Live remains inactive;
- Comms7 remains unchanged;
- no candidate ChatGPT App acceptance has yet been declared successful.

## Implementation campaign

The work was deliberately compressed into four packages.

### Package 1 — topology and repository preparation

Implemented:

- Common / Blue / Green / Live / Backup model;
- preservation and recovery checkpoints;
- four-repository local engineering environment;
- candidate validation;
- immutable release preparation;
- explicit activation gate.

The transitional Estate remained operational and recoverable.

### Package 2 — Estate Comms8 foundation

Implemented:

- versioned contracts;
- seven typed tools;
- persistence, leases, expiry, provenance, audit, idempotency, and reconciliation;
- provider-neutral Grace integration;
- local candidate vertical slice;
- browser-reuse assessment;
- external deployment plan.

### Package 3 — browser wake worker and orchestration sequence

Implemented:

- wake queue;
- browser worker;
- exact-conversation protection;
- fixed prompt submission;
- MCP-correlated completion;
- retry and recovery behavior;
- simulated full orchestration sequence.

### Package 4 — real connectivity, authenticated acceptance, deployment, and activation

Package 4 has included:

- diagnosis that no Estate Comms8 ChatGPT App existed;
- isolated candidate external endpoint design;
- HTTPS ingress and bounded tunnel design;
- separate credential model;
- namespace-only deployment tooling;
- DNS authority investigation;
- authenticated HostVerge browser access;
- exact candidate DNS record creation;
- continued candidate service/tunnel/Caddy restoration;
- pending real ChatGPT App acceptance;
- pending final Live activation gate.

## Important lessons

### 1. A browser wake is not an MCP invocation

Successful prompt submission proves only that a turn began.

Success must be established from the correlated MCP response.

### 2. Localhost is not a ChatGPT App endpoint

A local MCP service requires an externally reachable HTTPS boundary for ChatGPT web.

### 3. Authentication must be validated in the same browser context

A persistent profile path alone does not guarantee that an independent automation context shares the authenticated session.

### 4. CDP can be more reliable than profile reopening

Attaching to the live browser preserved the exact authenticated page and avoided profile-lock and cookie-context mismatch.

### 5. Operator action is sometimes cheaper than protocol reverse engineering

The candidate DNS record required one bounded control-panel action. Continuing to reverse-engineer StackCP’s mutation protocol would not have advanced the primary Estate objective proportionally.

### 6. Fail-closed gates were valuable

Codex repeatedly stopped before:

- migration with an unhealthy Estate;
- unexplained database mutation;
- Live activation;
- external deployment without authority;
- DNS mutation without verified scope;
- browser actions without authenticated context.

Those stops prevented unbounded infrastructure changes while still allowing substantial autonomous work.

## Remaining acceptance work

Before Estate Comms8 can be promoted:

1. Start and stabilize the Blue candidate MCP service.
2. Establish and verify the bounded SSH tunnel.
3. Restore and verify the candidate Caddy route.
4. Confirm public HTTPS reaches the candidate VPS after DNS caches expire.
5. Verify unauthenticated access returns `401`.
6. Verify authenticated `tools/list` exposes exactly seven tools.
7. Connect the Estate Comms8 candidate ChatGPT App.
8. Run a real correlated request through:

   ```text
   Grace
   → wake worker
   → ChatGPT
   → Estate Comms8 MCP
   → response
   → Grace reconciliation
   ```

9. Record actual approval behavior.
10. Exercise real-session recovery.
11. Prepare the final Live activation decision packet.
12. Receive explicit Steward authorization.
13. Activate the immutable Live release.
14. Validate canonical Estate services and Comms8.
15. Prove rollback.
16. Refresh and restore-test Backup.
17. Produce final campaign closeout and operator runbook.

## Final target state

The final target is a governed, durable, economical multi-provider engineering loop:

```text
Steward
    ↓
Grace
    ↓
Estate Comms8
    ↓
ChatGPT senior reasoning worker
    ↓
Grace-controlled provider routing
    ├── deterministic tools
    ├── local models
    ├── OpenHands
    ├── Qwen3-Coder
    └── Codex CLI escalation
    ↓
validation and reconciliation
    ↓
ChatGPT final review when required
    ↓
Grace closure or Steward escalation
```

The Estate remains the institution.

ChatGPT is a powerful reasoning worker inside that institution, not the institution itself.
