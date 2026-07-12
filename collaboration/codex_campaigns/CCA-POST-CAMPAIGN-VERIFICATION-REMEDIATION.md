# Chief Character Architect Post-Campaign Verification and Remediation Bundle

**Status:** Ready for Codex execution  
**Scope:** Verification and repair of merged Campaigns 01 through 07, covering WP-4043 through WP-4107  
**Authority:** Repository governance remains authoritative. This bundle repairs implementation gaps only; it does not redesign settled institutions.

## Objective

Audit the merged implementations from PRs #307 through #317 against the original work-package requirements, repair confirmed omissions and integration defects, restore full-suite validation, and produce one evidence-backed completion report.

Do not reimplement the campaigns from scratch. Preserve working code, extend canonical systems in place, and remove or consolidate duplicate mechanisms only where repository evidence confirms overlap.

## Verified campaign implementations

- PR #307: WP-4043 resident runtime identity composition
- PR #308: WP-4044 through WP-4052 resident foundation
- PR #309: WP-4054 through WP-4062 continuity and runtime operations
- PR #310: WP-4063 through WP-4072 memory and relationships
- PR #313: WP-4073 through WP-4082 visual architecture
- PR #315: WP-4083 through WP-4092 presence and culture
- PR #316: WP-4093 through WP-4102 affinity and growth
- PR #317: WP-4103 through WP-4107 Steward awareness

## Required repairs

### R1. Restore repository-wide test collection and validation

The campaign PRs repeatedly reported that full `pytest` collection was blocked by duplicate test-module basenames under `collaboration/workstreams/**` and `tests/**`.

1. Reproduce the collection failure on current `main`.
2. Identify every duplicate/import-file-mismatch source.
3. Repair discovery without deleting historical evidence or disabling legitimate tests.
4. Prefer unique module names, package isolation, or a narrowly governed pytest configuration.
5. Run the full suite after repair.
6. Record all remaining failures individually with ownership and whether they pre-existed these campaigns.

Completion requires a clean test collection. A focused-test pass is not sufficient.

### R2. Correct lifecycle and operational-availability leakage

Grace is appointed Director of Operations but is still Helen-owned onboarding and is not yet live, gateway-exposed, Open WebUI validated, or Steward-authorized for full operational service.

1. Ensure resident registry snapshots, identity composition, conference-room participation, relationship context, visual/presence projections, and tests distinguish appointment from operational availability.
2. Do not expose Grace as an active conversational/runtime participant until the canonical lifecycle, gateway, validation, and Steward-authorization evidence all permit it.
3. Preserve future-state visual or architectural records only when clearly labeled planned, onboarding, placeholder, or non-operational.
4. Replace tests that seed Grace as unconditionally active when the test is intended to represent current Estate state.
5. Add regression tests for appointed-but-not-operational residents.

Do not independently activate Grace.

### R3. Stop treating `pending/` as authoritative unfinished-work truth

The pending directory contains historical lifecycle residue and cannot be used as a reliable active-backlog count.

1. Remove or repair `grounded_fact_provider` facts that present raw `pending/` counts as current pending work.
2. Use an existing canonical lifecycle/completion/readiness source if available.
3. Where no reliable source exists, return `unknown` with diagnostics rather than a misleading count.
4. Add tests proving merged/completed packages remaining in `pending/` are not reported as unfinished.
5. Do not create a parallel work-package lifecycle institution.

### R4. Consolidate relationship-state architecture

Current merged code appears to contain overlapping relationship mechanisms:

- `estate.core.relationship_graph` with hard-coded public/private edges;
- `ResidentMemoryRuntime.relationship_proposals` and relationship-class memories;
- `estate.core.resident_affinity_growth` with `runtime/resident_affinity/affinity_graph.json`.

1. Determine the repository-authoritative relationship institution and persistence model.
2. Produce a migration and compatibility plan before changing data.
3. Consolidate reads and writes behind one canonical service boundary.
4. Remove hard-coded relationship truth where canonical source artifacts exist.
5. Preserve privacy redaction, directional/asymmetric dimensions, evidence lineage, proposals, review, and no-authority effects.
6. Prevent the memory system, affinity system, and identity composer from silently diverging.
7. Add cross-module integration tests proving one update is observed consistently everywhere.

Do not create a fourth relationship system.

### R5. Complete WP-4054 through WP-4062 operational integration

Campaign 02 implemented local primitives but its own receipt recommends missing operator integration.

1. Verify each work package has an actual callable runtime path, not only a helper function.
2. Integrate the required primitives into existing CLI, Office, gateway, scheduler, or runtime surfaces where the original packages require operational use.
3. Specifically verify commissioning/decommissioning uses the existing canonical lifecycle implementation and is not merely mentioned in documentation.
4. Verify the stateful Chat Runner can resume persisted jobs after process restart, enforce bounded prompts, expose pause/resume/cancel/manual takeover, and produce completion evidence.
5. Wire monitoring summaries into an existing Operations surface without creating a new dashboard institution.
6. Add end-to-end tests from operator invocation through durable artifact output.

### R6. Harden memory, audit, and concurrency behavior

1. Make durable JSON writes atomic where they are currently direct overwrite operations.
2. Add locking or conflict detection for concurrent memory, affinity, growth, awareness, and presence writes where applicable.
3. Ensure append-only ledgers reject malformed lines explicitly instead of silently discarding them.
4. Replace string-name authorization checks with canonical authority/capability checks where repository services exist.
5. Verify correction, supersession, retirement, quarantine, rollback, and audit evidence remain consistent after restart.
6. Add corruption, concurrent-write, and recovery tests.

### R7. Complete visual runtime beyond seed manifests

Campaign 04 installed manifests and validation, but verify the original package requirements for operational management.

1. Add governed create/update/review/approve/retire workflows for visual identity, wardrobe, locations, poses, portraits, gallery records, scenes, archive records, and timeline events where required.
2. Preserve canonical resident IDs; normalize name aliases such as `grace` and `evelyn` to registry identities without losing compatibility.
3. Mark placeholder assets and planned residents unmistakably.
4. Verify referenced asset paths exist or are explicitly declared future/restricted placeholders.
5. Add versioning, provenance, approval state, archive linkage, and rollback for material visual changes.
6. Integrate dynamic scene generation with the existing provider-routing/image workflow only as a governed request; do not create a second image provider system.
7. Add tests for missing assets, inactive residents, restricted material, lifecycle transitions, and historical continuity.

### R8. Repair presence and culture source integrity

1. Ensure ambient activity and occupancy consume canonical operational availability, not appointment alone.
2. Review seeded traditions, running jokes, culture memories, annual events, and proposals for actual evidence.
3. Quarantine or relabel invented/example seed content as demonstration data unless verified canonical sources support it.
4. Ensure simulated or inferred activity can never become durable memory, relationship change, attendance evidence, or completed-work evidence.
5. Add freshness, stale-source, privacy, and operational-status regression tests.
6. Confirm annual-event templates do not become calendar events without the proper existing authority path.

### R9. Complete Steward-awareness governance for WP-4103 through WP-4107

The current implementation is useful but materially narrower than the source packages.

Implement or repair all of the following:

1. Per-preference evidence records with source, timestamp, confidence, scope, last-confirmed, and status.
2. Explicit Steward instructions outrank inference; one observation cannot create a durable global preference.
3. Separate global, office, project, session, and surface scopes.
4. APIs to propose, confirm, supersede, retire, lock, reset, and reject preferences/adaptations.
5. Append-only audit records for profile, communication-mode, adaptation, support, and review changes.
6. Sensitive-field rejection for intimate, medical, financial, or unrelated personal information.
7. Explainable communication-mode selection with persisted rationale and override support.
8. Resident-specific voice preservation and tests against homogenization and sycophancy.
9. Drift thresholds, rollback, and review surfaces for persistent adaptations.
10. Support-trigger evidence, quiet/normal/urgent levels, declined-support suppression, and urgent-blocker exceptions.
11. Relationship reviews that distinguish verified fact, resident interpretation, inference, uncertainty, and contradiction.
12. Per-resident asymmetric reviews, privacy boundaries, correction/redaction/appeal, explicit approval before persistent calibration, and no fabricated affection or consent.
13. Replace simplistic majority-count learning with deterministic evidence weighting and contradiction handling.

### R10. Normalize completion receipts and lifecycle evidence

Campaign receipts currently use inconsistent paths and formats (`completions/`, `completed/`, Markdown, JSON, `codex_done`, and `implemented`).

1. Discover the existing canonical completion-receipt and lifecycle standard.
2. Normalize Campaign 01 through 07 evidence to that standard without destroying historical receipts.
3. Create compatibility pointers or migration records where necessary.
4. Ensure every WP from 4043 through 4107 has traceable implementation, tests, PR/commit, validation status, operational status, and acceptance status.
5. Do not move files merely because they reside in `pending/` unless the canonical lifecycle process authorizes that transition.

## Validation requirements

At minimum run:

1. Full repository test collection and full test suite.
2. Focused suites for identity, foundation, runtime operations, memory, visual runtime, presence/culture, affinity/growth, and Steward awareness.
3. Static compilation/type checks used by the repository.
4. Schema validation for all new or modified JSON schemas and representative artifacts.
5. Restart/recovery tests for durable runtimes.
6. Cross-campaign integration tests covering:
   - appointed but non-operational resident handling;
   - identity -> memory -> relationship/affinity consistency;
   - visual/presence filtering by lifecycle state;
   - Steward preference evidence -> communication/adaptation/support/review;
   - completion lifecycle not inferred from directory location.

## Stop conditions

Stop and report instead of guessing when:

- repository governance identifies a different canonical institution than expected;
- migration would destroy or silently reinterpret durable relationship, memory, or lifecycle evidence;
- Grace activation or Steward authorization would be required;
- a repair would create a parallel registry, queue, scheduler, memory system, relationship system, visual asset system, or authority path;
- full-suite failures reveal unrelated architectural defects too broad for this bundle.

## Deliverables

Produce one coherent repair branch and one pull request containing:

1. Repairs and migrations.
2. Tests and validation evidence.
3. `operations/character_architecture/CCA_Post_Campaign_Verification_Report.md` with a package-by-package ledger for WP-4043 through WP-4107:
   - implemented as specified;
   - implemented with bounded deviation;
   - repaired;
   - still blocked;
   - operationally unavailable;
   - Steward acceptance required.
4. A machine-readable completion receipt using the canonical repository standard.
5. Exact remaining blockers and recommended next actions.

## Completion standard

This remediation bundle is complete only when full test collection works, all repaired focused tests pass, every material gap above is either repaired or explicitly blocked with repository evidence, and no campaign is described as fully operational merely because its pull request merged.