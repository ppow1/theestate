# ESTATE-CAP-001 Implementation Report

Date: 2026-07-31

## Result

The Estate-wide capability onboarding standard, executor-neutral implementation
template, operator runbook, readiness checklist, worked-example overlays, and
machine-checkable manifest/lint contract are complete on the branch
`architecture/estate-capability-onboarding-standard`.

Starting main: `e9acd9d1d26ba92fdf3ba1e9bc282f747fcbac9e`

## Canonical surfaces reused

- Provider identity and capability discovery: `config/providers/catalog.json`
  and `estate.core.provider_catalog`.
- Capability source surface: `data/registry/capabilities.json`.
- Read-only derived inventory: `estate.core.estate_capability_registry`.
- Capability lifecycle terminology: `docs/governance/Capability_Lifecycle_States_v1.md`.
- Grace/Helen capability-gap lifecycle: existing Engineering capability
  enablement lifecycle and composition records.
- PTM readiness, Engineering authority, Operations decision, Dispatch,
  adapter handoff, provider receipts, reconciliation, and Grace terminal
  evidence: existing versioned contracts and production paths.
- Local service manifests: existing `runtime/ai_services` manifests.

No complete canonical resident capability/tool manifest existed. The smallest
compatible closed contract was added at
`schemas/residents/resident_capability_manifest_v1.schema.json`. It enumerates
resident-facing capability maturity, availability, dispatchability, bindings,
classification, I/O, limitations, authorization requirements, evidence, and
optional implementation-worker requirements. It does not replace the provider
catalog or derived capability registry.

## Deliverables

- `docs/architecture/Estate_Capability_Onboarding_Standard.md`
- `collaboration/work_packages/templates/ESTATE_CAPABILITY_ONBOARDING_IMPLEMENTATION_TEMPLATE.md`
- `docs/operations/Estate_Capability_Onboarding_Runbook.md`
- `docs/operations/checklists/Estate_Capability_Onboarding_Readiness_Checklist.md`
- `docs/operations/examples/Estate_Capability_Onboarding_Worked_Examples.md`
- `schemas/residents/resident_capability_manifest_v1.schema.json`
- `src/estate/core/work_package_validation.py` (bounded onboarding-section lint)
- `src/estate/cli/main.py` (`validate-capability-onboarding` command)
- `tests/test_estate_capability_onboarding.py`

The maturity model adopted is Level 0 Concept, Level 1 Registered, Level 2
Provider Available, Level 3 Governed, Level 4 Operational, and Level 5
Institutionally Accepted. Evidence expiry can reduce current dispatchability
without rewriting historical maturity evidence. Institutional acceptance is
always separate.

Executor neutrality is ensured by specifying contracts, authority, evidence,
tests, runtime synchronization, rollback, and stop conditions rather than
worker-specific commands or memory. Codex, Qwen Coder, human Engineering,
Grace, and Helen are named only as possible contract-satisfying executors;
provider-specific examples are explicitly designs and were not implemented.

Grace consumes existence, maturity, availability, dispatchability,
authorization, limitations, and enabling-project state. Helen consumes owner,
qualification, adapter/wrapper presence, health, capacity, freshness, and gap
state. The existing inquiry -> assessment -> gap/specification -> enabling
project -> registration -> re-evaluation -> Grace resumption lifecycle is
preserved.

## Validation

- Focused onboarding/schema/work-package tests: 36 passed.
- Bounded catalog, capability, PTM, Grace/Helen, Dispatch, handoff, and
  onboarding tests: 58 passed.
- Manifest validated with Draft 2020-12 and `FormatChecker`.
- Canonical package lint passed for this package and the onboarding template.
- Python compilation passed for changed modules.
- `git diff --check` passed.
- Paper exercise: Helen identifies a missing worker capability, returns a gap,
  Grace receives an enabling-project proposal, and later resumes after
  registration/re-evaluation: passed.
- Paper exercise: an already Level 4 capability is discoverable and Grace
  resumes without another implementation: passed.
- Surface review found no duplicate provider catalog, capability registry,
  Dispatch path, PTM system, or personnel system proposed.

Two unrelated existing CLI tests remain red in the broad matrix:
`test_capability_lifecycle_cli_registration` and
`test_cli_writes_visualization_outputs`. Both use a temporary fixture root but
the current CLI root-discovery behavior resolves the checkout and reports six
real capabilities instead of the one fixture capability. The failures are
unchanged by this package and do not exercise the new schema or lint.

## Deferred architecture decisions

The Steward/Chief Architect may later decide whether resident-facing runtime
surfaces should consume the new manifest directly, how existing legacy
capability records are migrated or superseded, and which future provider
overlays should seek Level 4 acceptance. This package does not implement
Qwen Coder, Whisper, ComfyUI live execution, Historian, Legal, or any new
provider catalog behavior.

No live provider was invoked. No model, service, historical evidence, or
institutional acceptance state was changed.
