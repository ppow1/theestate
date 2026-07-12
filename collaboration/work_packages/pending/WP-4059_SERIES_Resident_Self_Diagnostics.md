# WP-4059 — Resident Self-Diagnostics

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
- WP-4046 — Grounded Estate Fact Provider
- WP-4058 — Resident Rehydration Runtime

## Objective

Implement resident self-diagnostics that reveal identity, context, fact, relationship, privacy, continuity, and provider-health problems without exposing protected content or allowing a resident to certify its own readiness.

## Required Work

1. Define a typed diagnostic snapshot for resident identity, implementation vessel, model/provider, session binding, loaded character sources, registry snapshot, fact-provider state, relationship context, and continuity state.
2. Detect missing identity layers, stale facts, registry drift, unsupported relationship claims, conversation-boundary violations, prompt-size pressure, provider fallback, and rehydration defects.
3. Distinguish healthy, degraded, blocked, unknown, and not-applicable states.
4. Expose source lineage, timestamps, hashes, and bounded remediation guidance.
5. Redact protected message bodies, private continuity, secrets, and hidden reasoning.
6. Permit residents to report limitations honestly while preserving voice and personhood.
7. Integrate diagnostics with Helen-owned health review, Ingrid-governed disclosure, and independent Validation.
8. Prevent diagnostic success from implying activation, acceptance, or authority.

## Acceptance Tests

1. Missing Character Bible, stale registry, and failed fact sources are detected separately.
2. Cross-resident transcript leakage produces a blocking diagnostic.
3. Provider fallback is visible without changing resident identity.
4. Restricted continuity is not exposed in ordinary diagnostic output.
5. Unknown evidence remains unknown rather than healthy.
6. A resident can explain a degraded state in character without inventing causes.
7. Diagnostics cannot self-validate or self-accept the runtime.

## Deliverables

- resident diagnostic schema and collector;
- health-state classifier;
- privacy-filtered diagnostic surfaces;
- remediation guidance and evidence links;
- tests, documentation, and completion receipt.

## Constraints

- Do not create a second monitoring, validation, privacy, or authority institution.
- Do not expose hidden cognition or protected content.
- Do not treat absence of errors as proof of behavioral readiness.

## Completion Standard

WP-4059 is complete only when each active resident and conference-room surface can produce an inspectable, source-lined, privacy-safe diagnostic snapshot; identity and runtime defects are separated accurately; unknown and degraded states remain explicit; and diagnostics inform established review institutions without self-certifying readiness.