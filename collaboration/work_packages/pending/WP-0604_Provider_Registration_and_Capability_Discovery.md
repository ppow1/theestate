# WP-0604 - Provider Registration and Capability Discovery

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first shared provider registration and capability discovery layer for the Estate.

The Estate now has planning-provider contracts, operational event/status work, Office visibility work, and Orchestrator intake work moving in parallel. This package creates the common provider catalog so future planning providers, execution providers, validation providers, documentation providers, research providers, and local model providers can advertise capabilities without creating duplicated registries or product-specific routing logic.

This package does not implement provider execution. It implements provider identity, capability description, registration, discovery, and CLI inspection.

## Required Reading

Read these before implementation:

- `AI_START_HERE.md`
- `AI_HINTS.md`
- `docs/governance/Estate_Orientation_Handbook.md`
- `docs/governance/Estate_Manual.md`
- `docs/governance/Estate_Vision_and_Architecture.md`
- `docs/governance/Capability_Lifecycle_States_v1.md`
- `docs/governance/Practical_Worker_Onboarding_Addendum.md`
- `docs/collaboration/Estate_Collaboration_Layer_v1.md`
- `docs/collaboration/Estate_Collaboration_Standard_v1.md`
- `docs/architecture/planning_pipeline.md`
- `docs/architecture/chatgpt_role_in_estate.md`
- `docs/architecture/chatgpt_vs_codex.md`
- `docs/architecture/execution_provider_operational_visibility_requirements.md`
- `collaboration/work_packages/pending/WP-0600_Planning_Provider_Framework.md`
- `collaboration/work_packages/pending/WP-0601_Operational_Event_Feed_and_Office_Status.md`
- `collaboration/work_packages/pending/WP-0603_Orchestrator_Intake_Contract.md`

If any of WP-0600 through WP-0603 have already been implemented, inspect their actual code and integrate with it. Do not duplicate their registries or models.

## Architectural Intent

Create one shared capability catalog for provider implementations.

The Estate should route work by capability and boundary, not by product name.

Examples:

- ChatGPT may advertise planning, governance drafting, documentation drafting, research, connector reasoning.
- Codex may advertise repository implementation and code editing.
- Ollama/local LLMs may advertise local reasoning, classification, review, summarization.
- Validation workers may advertise test execution and receipt generation.
- Future providers may advertise image generation, transcription, model selection, scheduling, or other capabilities.

Do not create a new office. This is infrastructure for future Orchestrator and Office visibility.

## Scope

Implement:

1. Provider descriptor model.
2. Provider capability model.
3. Provider registry/catalog loader.
4. Provider filtering and lookup functions.
5. Static provider catalog file or files.
6. CLI command to list providers.
7. CLI command to inspect one provider.
8. CLI command or helper to find providers by capability.
9. Runtime/status export for Office consumption.
10. Tests for descriptors, filtering, catalog loading, and CLI behavior.
11. Concise integration documentation.

## Out of Scope

Do not implement:

- provider execution,
- scheduling,
- full Orchestrator,
- live ChatGPT integration,
- live OpenAI API calls,
- Codex Bridge implementation,
- local Ollama invocation,
- Office UI changes,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new offices.

## Implementation Targets

Use existing repository conventions. Preferred files:

- `src/estate/core/provider_catalog.py`
- `src/estate/core/provider_capabilities.py`
- `tests/test_provider_catalog.py`
- `tests/test_provider_capabilities.py`
- `docs/integration/provider_registration_and_capability_discovery.md`

Preferred catalog path:

- `config/providers/catalog.json`

If the repository already has a better config or registry location, use it and document the actual path.

## Provider Descriptor Model

Implement and validate a provider descriptor with these fields:

- `provider_id` string, required
- `display_name` string, required
- `provider_type` string, required
- `implementation_kind` string, required
- `status` string, required
- `classification_ceiling` string, required
- `capabilities` list, required
- `allowed_context_classes` list, default empty
- `requires_boundary_review` boolean, default false
- `supports_events` boolean, default false
- `supports_artifacts` boolean, default false
- `supports_validation` boolean, default false
- `supports_offline` boolean, default false
- `requires_network` boolean, default false
- `cost_model` string, default `unknown`
- `routing_notes` string, optional
- `limitations` list, default empty
- `metadata` object, default empty

Allowed provider types:

- `planning`
- `execution`
- `validation`
- `documentation`
- `research`
- `classification`
- `media`
- `infrastructure`
- `mixed`

Allowed implementation kinds:

- `chatgpt`
- `codex`
- `local_llm`
- `python`
- `powershell`
- `github_actions`
- `manual`
- `future`
- `stub`
- `other`

Allowed statuses:

- `designed`
- `implemented`
- `operationally_validated`
- `institutionalized`
- `deprecated`
- `blocked`

Allowed classification ceilings:

- `Public`
- `Estate Internal`
- `Restricted`
- `Steward Only`
- `Local Only`

## Capability Model

Each capability should include:

- `capability_id` string, required
- `display_name` string, required
- `category` string, required
- `description` string, optional
- `input_artifacts` list, default empty
- `output_artifacts` list, default empty
- `requires_approval` boolean, default false
- `requires_validation` boolean, default false
- `supports_offline` boolean, default false
- `metadata` object, default empty

Initial capability IDs should include at least:

- `planning`
- `architecture_review`
- `governance_draft`
- `work_package_draft`
- `documentation_draft`
- `repository_implementation`
- `code_review`
- `test_execution`
- `audit_execution`
- `validation_receipt`
- `local_reasoning`
- `classification_review`
- `web_research`
- `connector_context_read`

Do not make this list final or exhaustive. Implement extension support while preserving validation of required fields.

## Initial Catalog Entries

Seed the catalog with descriptors for these providers:

1. `stub.planning.echo`
   - provider_type: `planning`
   - implementation_kind: `stub`
   - status: `implemented` if WP-0600 exists, otherwise `designed`
   - capabilities: planning, documentation_draft
   - supports_offline: true
   - requires_network: false

2. `chatgpt.planning.external`
   - provider_type: `planning`
   - implementation_kind: `chatgpt`
   - status: `designed`
   - capabilities: planning, architecture_review, governance_draft, work_package_draft, documentation_draft, web_research, connector_context_read
   - requires_network: true
   - requires_boundary_review: true

3. `codex.execution.cli`
   - provider_type: `execution`
   - implementation_kind: `codex`
   - status: `designed` or current repository-supported state if evidence exists
   - capabilities: repository_implementation, code_review
   - requires_boundary_review: true

4. `ollama.local.reasoning`
   - provider_type: `classification` or `mixed`
   - implementation_kind: `local_llm`
   - status: `designed` unless implementation evidence exists
   - capabilities: local_reasoning, classification_review
   - supports_offline: true
   - requires_network: false

5. `estate.audit.local`
   - provider_type: `validation`
   - implementation_kind: `powershell` or `python` based on existing audit implementation
   - status: current evidence-supported state
   - capabilities: audit_execution, validation_receipt
   - supports_offline: true

Do not overclaim status. If evidence is absent, use `designed`.

## CLI Requirements

Add commands using existing Estate CLI conventions.

Preferred commands:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat providers-list
.\estate.bat providers-show --provider-id chatgpt.planning.external
.\estate.bat providers-find --capability work_package_draft
```

Commands must:

- print concise human-readable output,
- support JSON output if existing CLI conventions support it,
- exit non-zero for missing provider ID,
- fail clearly on malformed catalog,
- avoid network calls.

If existing CLI routing uses different naming, follow existing conventions and document actual commands.

## Runtime/Office Export

Write or generate an Office-readable provider status artifact at:

- `runtime/providers/catalog_status.json`

This artifact should include:

- provider count,
- providers by type,
- providers by status,
- available capabilities,
- provider descriptors safe for Office display,
- generated_at timestamp.

Sensitive routing notes or limitations should be included only if safe. There should be no secrets in provider descriptors.

## Integration with WP-0600 and WP-0603

If WP-0600 exists, align planning provider registry with this catalog rather than creating two conflicting sources of truth.

If WP-0603 exists, ensure intake requests can refer to provider types, provider IDs, and required capabilities that match this catalog.

If either package is not implemented yet, document integration points and provide functions they can later call.

## Boundary Behavior

- Unknown classification ceiling fails.
- Unknown provider type fails.
- Unknown implementation kind fails.
- Unknown status fails.
- Unknown capability object missing required fields fails.
- Catalog must not include credentials, tokens, secrets, or private prompts.

## Tests

Add tests covering:

1. Valid provider descriptor accepted.
2. Missing provider ID rejected.
3. Unknown provider type rejected.
4. Unknown status rejected.
5. Valid capability accepted.
6. Capability missing ID rejected.
7. Catalog loads successfully.
8. Provider lookup by ID works.
9. Provider filtering by type works.
10. Provider filtering by capability works.
11. Office catalog status export is generated.
12. CLI providers-list succeeds.
13. CLI providers-show succeeds for known provider.
14. CLI providers-show fails for unknown provider.
15. CLI providers-find returns matching providers.

Do not require network access.

## Documentation

Create `docs/integration/provider_registration_and_capability_discovery.md` with:

- purpose,
- provider descriptor model,
- capability model,
- catalog path,
- CLI examples,
- Office export path,
- integration notes for planning providers,
- integration notes for Orchestrator intake,
- boundary notes,
- how to add future providers.

Keep it concise.

## Acceptance Criteria

Complete when:

- provider descriptor model exists,
- capability model exists,
- catalog loads from repository config,
- initial provider entries exist,
- provider lookup/filtering works,
- CLI list/show/find commands work,
- Office-readable catalog status export exists,
- tests pass,
- documentation exists,
- no new office or duplicate registry is created,
- WP-0600 and WP-0603 can integrate without redesign.

## Validation

Run targeted tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
python -m pytest tests/test_provider_catalog.py tests/test_provider_capabilities.py
.\estate.bat audit
```

If repository conventions require different commands, use those and report the actual commands.

Produce an implementation summary with:

- files changed,
- tests run,
- audit result,
- provider catalog path,
- blocked items,
- recommended follow-up package.

## Do Not Touch

Do not modify:

- archived institutional memory,
- Alfred responsibility definitions,
- Helen responsibility definitions,
- Ingrid responsibility definitions,
- provider execution code except import-safe integration,
- Office UI components.

## Expected Follow-On Packages

Do not implement these now:

- WP-0605 Office decision controls for pending and blocked intake.
- WP-0606 Orchestrator scheduling skeleton.
- WP-0607 Provider health checks and capacity reporting.
