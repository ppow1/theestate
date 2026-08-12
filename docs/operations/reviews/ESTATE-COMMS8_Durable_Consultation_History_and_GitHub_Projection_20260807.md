# Estate Comms8 Durable Consultation History and GitHub Projection

Date: 2026-08-07

## Decision

The Estate consultation SQLite store is the authoritative reasoning history. Comms8 remains the authoritative transport/lifecycle system. GitHub is an asynchronous, idempotent human-readable projection and is not required for reasoning or context recovery.

## Implemented contract

- Bounded local reads: root, turn range, latest turns, compact summary, and `CONTEXT_REQUIRED` responses.
- Searchable consultation fields remain available through the existing store indexes, including Comms8 request, workflow, PTM project, status, and tags.
- Compact summaries persist independently of turn transcripts and are updated after meaningful response/validation events.
- Transport attempts remain separate from logical consultation turns. A retry creates a new `ec8-*` attempt without allocating a continuation.
- Projection uses one stable artifact per consultation root and updates it idempotently.
- Projection failures leave local truth available and mark the projection pending/failed; they do not block Comms8 processing.

## Live acceptance

Existing completed consultation history was used; no new reasoning request was created.

| Logical turn | State | Comms8 request | Transport history |
|---|---|---|---|
| `3.00` | resolved | `ec8-61b2b5c9191b4822` | `ec8-8db54efb5c234f0a` expired under `codex-workmode-estate-reasoner`; replacement resolved under `chatgpt` |
| `3.01` | resolved | `ec8-a68e19268f9e444e` | resolved under `chatgpt` |

The original expired request remains immutable historical evidence. The local store reconstructs both turns and both 3.00 transport attempts, persists a compact summary, and returns a bounded latest-turn query plus a `CONTEXT_REQUIRED` retrieval envelope.

The single GitHub projection is [issue #518](https://github.com/ppow1/theestate/issues/518). Repeated projection updates that issue rather than creating a duplicate. SQL records for 3.00 and 3.01 reference the issue with projection status `published`.

## Context contract

The worker and Grace use the local store in this order: current Comms8 envelope, compact summary, bounded local turn retrieval, and GitHub only as optional archive evidence. A context request identifies the consultation root, requested range/latest count, reason, and selected turn metadata. Missing context is reported as `CONTEXT_REQUIRED`; the system does not improvise.

## PTM and rollover

PTM remains reference-only and its semantics are unchanged. Standalone consultations remain valid. Existing logical `.99` rollover rules and predecessor lineage remain enforced for future roots; physical ChatGPT conversations are not required to reconstruct the consultation.

## Activation

- Consultation-store/projection code: **REQUIRED** to relaunch any long-lived consultation or mailbox worker process that imports this code; verify the process startup version and a successful local history read.
- Mailbox worker relaunch: **CONDITIONAL**—required only for a continuously running worker using the changed code.
- Grace Resident Gateway restart: **CONDITIONAL**—required only if the deployed gateway imports the changed store/loop code; not required for read-only store/projection acceptance.
- Open WebUI restart, Comms8 restart, MCP adapter restart, ChatGPT reconnect, dedicated browser restart, and workstation reboot: **NOT REQUIRED**.

ACTIVATION REQUIRED:
Relaunch the consultation/mailbox worker if it is persistent, then verify it can read consultation `3.00` and bounded turns `3.00–3.01` from the canonical SQLite store. Restart Grace only if its running process is being upgraded to import these changes. No UI or infrastructure restart is required.

