# WP-4061 — Resident Maturation Install Handoff and Commissioning

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4043 through WP-4060, excluding the pre-existing WP-4053 dependency where already installed

## Objective

Install, integrate, and commission the Resident Maturation runtime as one governed capability set, proving that authored and implemented components are actually connected, operational, validated, and ready for Steward acceptance.

## Required Work

1. Inventory completion receipts, validation evidence, install manifests, migrations, configuration, and rollback notes for the full Resident Maturation series.
2. Reconcile shared hot-file changes and ensure all packages use the canonical identity composer, registry snapshot, fact provider, conversation isolation, messaging, mailbox, relationship, conference-room, continuity, diagnostic, and monitoring paths.
3. Install required runtime components and configurations without duplicating systems or bypassing governance.
4. Migrate existing resident data and derived indexes deterministically, preserving rollback and source lineage.
5. Run end-to-end tests for Alfred, Helen, Grace, Ingrid, Evelyn, and the conference room across model/provider changes and runtime restart.
6. Verify identity, factual grounding, privacy, messaging, mailbox, relationships, conference-room disclosure, renewal, diagnostics, and monitoring together.
7. Update the Activation Ledger and operational documentation with exact installed, activated, blocked, and deferred states.
8. Produce commissioning and rollback receipts; do not claim acceptance on behalf of the Steward.

## Acceptance Tests

1. Every active resident loads identity and facts through the canonical shared runtime.
2. Separate resident chats and conference-room context remain isolated.
3. Canonical messages, mailbox views, routing, and acknowledgments agree.
4. Relationship context is individualized and privacy-filtered.
5. Model changes preserve resident identity and do not merge histories.
6. Reflection, continuity generation, validation, rehydration, diagnostics, and monitoring execute with inspectable evidence.
7. Runtime restart preserves durable state and regenerates derived artifacts correctly.
8. Rollback returns to the prior known-good state without corrupting canonical data.

## Deliverables

- install and migration plan;
- integrated runtime configuration;
- end-to-end commissioning suite;
- Activation Ledger and documentation updates;
- commissioning, limitation, and rollback receipts.

## Constraints

- Do not equate staged code with installed or accepted capability.
- Do not create parallel resident systems during integration.
- Do not bypass independent Validation or Steward acceptance.
- Do not silently discard incompatible historical data.

## Completion Standard

WP-4061 is complete only when the Resident Maturation components are installed through the canonical Estate runtime, end-to-end behavior is proven with inspectable evidence, rollback is available, Activation Ledger state is accurate, remaining limitations are explicit, and the capability is ready for—but not falsely declared to have received—Steward acceptance.