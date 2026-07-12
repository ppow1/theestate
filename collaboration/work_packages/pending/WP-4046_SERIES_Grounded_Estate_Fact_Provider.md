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

##