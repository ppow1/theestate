# Capability Dependency Visualization

Read-only visualization for Mission Control and architectural review. This artifact is not a source of truth.

Generated: 2026-07-05T16:04:51+00:00

## Summary
- Nodes: 6
- Capability nodes: 6
- Edges: 0
- Warnings: 19
- Readiness: {'ready': 6}

## Nodes

### RTX 4090 CUDA (CAP-000001)
- Type: capability
- Readiness: ready
- Implementation state: Operational
- Lifecycle state: Implemented
- Validation state: evidence_found
- Upstream dependencies: None explicitly recorded
- Downstream dependents: None explicitly recorded
- Authoritative artifact: `data/registry/capabilities.json`
- Source links: `data/registry/capabilities.json`, `Local AI Workstation`, `A:\AI`, `observations/ai_environment_2026-06-29_23-47-42.json`, `estate_ledger/ledger.md`, `development/devlog.md`, `docs/service_catalog.md`, `README.md`, `runtime/validation/operational_validation_report.json`
  - Warning: unresolved_source_link — Source artifact is not present: Local AI Workstation
  - Warning: unresolved_source_link — Source artifact is not present: A:\AI
  - Warning: no_explicit_relationships — No explicit upstream or downstream dependency relationship is available.

### Kokoro TTS (CAP-000002)
- Type: capability
- Readiness: ready
- Implementation state: Operational
- Lifecycle state: Implemented
- Validation state: evidence_found
- Upstream dependencies: None explicitly recorded
- Downstream dependents: None explicitly recorded
- Authoritative artifact: `data/registry/capabilities.json`
- Source links: `data/registry/capabilities.json`, `A:\AI\TTS`, `observations/ai_environment_2026-06-29_23-47-42.json`, `estate_ledger/ledger.md`, `development/devlog.md`, `docs/service_catalog.md`, `runtime/validation/operational_validation_report.json`
  - Warning: unresolved_source_link — Source artifact is not present: A:\AI\TTS
  - Warning: no_explicit_relationships — No explicit upstream or downstream dependency relationship is available.

### F5-TTS (CAP-000003)
- Type: capability
- Readiness: ready
- Implementation state: Operational
- Lifecycle state: Implemented
- Validation state: evidence_found
- Upstream dependencies: None explicitly recorded
- Downstream dependents: None explicitly recorded
- Authoritative artifact: `data/registry/capabilities.json`
- Source links: `data/registry/capabilities.json`, `A:\AI\TTS\F5-TTS`, `observations/ai_environment_2026-06-29_23-47-42.json`, `estate_ledger/ledger.md`, `development/devlog.md`, `docs/service_catalog.md`, `runtime/validation/operational_validation_report.json`
  - Warning: unresolved_source_link — Source artifact is not present: A:\AI\TTS\F5-TTS
  - Warning: no_explicit_relationships — No explicit upstream or downstream dependency relationship is available.

### ComfyUI (CAP-000004)
- Type: capability
- Readiness: ready
- Implementation state: Installed
- Lifecycle state: Implemented
- Validation state: evidence_found
- Upstream dependencies: None explicitly recorded
- Downstream dependents: None explicitly recorded
- Authoritative artifact: `data/registry/capabilities.json`
- Source links: `data/registry/capabilities.json`, `A:\AI\ComfyUI`, `observations/ai_environment_2026-06-29_23-47-42.json`, `estate_ledger/ledger.md`, `development/devlog.md`, `docs/service_catalog.md`, `runtime/validation/operational_validation_report.json`
  - Warning: unresolved_source_link — Source artifact is not present: A:\AI\ComfyUI
  - Warning: no_explicit_relationships — No explicit upstream or downstream dependency relationship is available.

### FFmpeg / FFplay (CAP-000005)
- Type: capability
- Readiness: ready
- Implementation state: Operational
- Lifecycle state: Implemented
- Validation state: evidence_found
- Upstream dependencies: None explicitly recorded
- Downstream dependents: None explicitly recorded
- Authoritative artifact: `data/registry/capabilities.json`
- Source links: `data/registry/capabilities.json`, `A:\AI\Tools\FFmpeg`, `observations/ai_environment_2026-06-29_23-47-42.json`, `estate_ledger/ledger.md`, `development/devlog.md`, `docs/service_catalog.md`, `runtime/validation/operational_validation_report.json`
  - Warning: unresolved_source_link — Source artifact is not present: A:\AI\Tools\FFmpeg
  - Warning: no_explicit_relationships — No explicit upstream or downstream dependency relationship is available.

### Whisper (CAP-000006)
- Type: capability
- Readiness: ready
- Implementation state: Pending Install
- Lifecycle state: Designed
- Validation state: evidence_found
- Upstream dependencies: None explicitly recorded
- Downstream dependents: None explicitly recorded
- Authoritative artifact: `data/registry/capabilities.json`
- Source links: `data/registry/capabilities.json`, `A:\AI`, `estate_ledger/ledger.md`, `development/devlog.md`, `docs/service_catalog.md`, `observations/ai_environment_2026-06-29_23-47-42.json`, `runtime/validation/operational_validation_report.json`
  - Warning: unresolved_source_link — Source artifact is not present: A:\AI
  - Warning: no_explicit_relationships — No explicit upstream or downstream dependency relationship is available.

## Edges
- No explicit capability dependency edges were found.

## Limitations
- Only explicit capability registry dependencies and explicit dependency graph edges are shown.
- No dependency is inferred from prose, naming, ordering, implementation references, or service names.
- Missing dependency metadata creates warnings and isolated nodes rather than fabricated edges.

## Warnings
- empty_capability_dependency_metadata: Capability declares no explicit dependencies.
- empty_capability_dependency_metadata: Capability declares no explicit dependencies.
- empty_capability_dependency_metadata: Capability declares no explicit dependencies.
- empty_capability_dependency_metadata: Capability declares no explicit dependencies.
- empty_capability_dependency_metadata: Capability declares no explicit dependencies.
- empty_capability_dependency_metadata: Capability declares no explicit dependencies.
