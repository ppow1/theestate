# WP-0535 - Engineering Provider Health and Telemetry Runtime

Status: Proposed
Priority: High
Owner: Chief Architect #5
Mode: PARALLEL-INDEPENDENT
Classification: Estate Internal

## Mission

Implement a provider-health runtime that determines whether each engineering provider is operationally healthy enough to receive work.

This package complements:

- WP-0532: Engineering Capacity Runtime
- WP-0533: Engineering Provider Routing
- WP-0534: Codex CLI Capability Discovery and Polling Policy

Capacity, capability, and health must remain separate evidence domains.

## Required Reading

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Institutional_Operations_Doctrine.md
docs/governance/PowerShell_Session_Output_and_Handoff_Standard.md
src/estate/core/engineering_capacity_runtime.py
src/estate/core/engineering_provider_routing_runtime.py
src/estate/core/codex_status_cost_characterization.py
runtime/provider_registry/codex/capabilities.json
runtime/provider_registry/codex/polling_policy.json
```

Inspect current provider adapters, local Ollama integration, Codex bridge artifacts, execution-provider contracts, and Office engineering-capacity outputs before implementation.

## Required Providers

Initial provider support must include:

```text
codex_cloud_web
codex_cli_openai
local_ollama_gpu
local_gpu_runtime
```

Unsupported or unavailable providers must report `unknown` or `offline` truthfully rather than being omitted or fabricated.

## Normalized Health Contract

Create a normalized provider-health record containing at least:

```text
schema_version
provider_id
provider_type
observed_at
last_success_at
last_failure_at
availability
authentication_state
runtime_state
capability_registry_state
capacity_state
latency_ms
recent_success_count
recent_failure_count
recent_failure_rate
consecutive_failures
queue_depth
active_jobs
provider_version
last_discovery_at
last_capacity_snapshot_at
stale_after_seconds
is_stale
health_state
health_reasons
warnings
evidence_refs
recommended_for_dispatch
```

Allowed primary health states:

```text
healthy
degraded
offline
maintenance
unknown
```

## Health Evaluation Rules

At minimum, evaluate:

- executable or endpoint availability;
- authentication readiness;
- capability registry freshness;
- capacity snapshot freshness;
- last successful operation;
- recent failures and consecutive-failure streaks;
- observed latency;
- queue depth and saturation indicators;
- provider version visibility where available;
- stale or missing evidence;
- maintenance or explicit disablement state.

Do not mark a provider healthy solely because its executable exists.

Do not perform billable prompt execution merely to test health.

Codex status or remote probes must obey the polling policy produced by WP-0534. Unknown probe cost means no automatic live polling.

## Runtime Outputs

Create:

```text
runtime/provider_health/current.json
runtime/provider_health/providers/codex_cloud_web.json
runtime/provider_health/providers/codex_cli_openai.json
runtime/provider_health/providers/local_ollama_gpu.json
runtime/provider_health/providers/local_gpu_runtime.json
runtime/provider_health/history.jsonl
operations/engineering_capacity/provider_health.md
```

Writes must be atomic where practical. History records must be append-only.

## Implementation

Create a dedicated runtime, preferably:

```text
src/estate/core/engineering_provider_health_runtime.py
```

The runtime must:

1. collect only approved read-only evidence;
2. normalize provider-specific observations;
3. calculate deterministic health states;
4. preserve evidence references;
5. distinguish unavailable, stale, unauthenticated, saturated, and failed providers;
6. expose current and historical health artifacts;
7. avoid direct dispatch or authorization decisions.

## CLI

Add focused CLI commands such as:

```text
python -m estate.cli.main engineering-provider-health collect --json
python -m estate.cli.main engineering-provider-health status --json
python -m estate.cli.main engineering-provider-health provider --id codex_cloud_web --json
python -m estate.cli.main engineering-provider-health report
```

The CLI must not submit prompts, start provider jobs, or bypass WP-0534 polling restrictions.

## Routing Integration

Update the provider-routing runtime so recommendations consume:

```text
capability evidence
+ capacity evidence
+ health evidence
+ routing policy
```

A provider must not be recommended when:

- required capability is absent;
- health is `offline`;
- authentication is invalid;
- capacity is exhausted;
- evidence is stale beyond policy;
- provider is explicitly disabled or in maintenance.

`degraded` providers may be recommended only when policy allows and the recommendation clearly explains the risk.

Routing remains recommendation-only unless an existing governed dispatch path explicitly authorizes execution.

## Office Integration

Expose provider-health artifacts to the existing Engineering Capacity dashboard or Office consumer contract.

The Office must display, at minimum:

- provider name;
- health state;
- authentication state;
- freshness;
- last success;
- last failure;
- latency;
- failure rate;
- active jobs and queue depth;
- capacity reference;
- reasons and warnings;
- dispatch recommendation eligibility.

The Office must not contain provider-health computation logic.

## Tests

Create focused tests, preferably:

```text
tests/test_engineering_provider_health_runtime.py
tests/test_engineering_provider_health_routing_integration.py
```

Tests must prove:

- healthy provider classification;
- degraded provider classification;
- offline provider classification;
- authentication failure handling;
- stale capability evidence handling;
- stale capacity evidence handling;
- consecutive-failure thresholds;
- latency degradation;
- queue saturation handling;
- local provider health without network calls;
- Codex health without prompt submission;
- WP-0534 polling policy enforcement;
- routing excludes unhealthy providers;
- degraded routing produces explicit warnings;
- deterministic output;
- append-only history;
- malformed evidence does not crash the runtime.

Use fake probes, fake process results, and temporary Estate roots. No live provider work is required for deterministic validation.

## Documentation

Create:

```text
docs/integration/engineering_provider_health_runtime.md
```

Document:

- health schema;
- evidence sources;
- evaluation thresholds;
- freshness rules;
- routing integration;
- polling-policy compliance;
- failure and recovery behavior;
- extension process for future providers.

## Validation

Register a WP-0535 validation recipe.

Likely validation commands:

```text
python -m py_compile src/estate/core/engineering_provider_health_runtime.py src/estate/core/engineering_provider_routing_runtime.py
pytest -q tests/test_engineering_provider_health_runtime.py tests/test_engineering_provider_health_routing_integration.py tests/test_engineering_provider_routing_runtime.py tests/test_engineering_capacity_runtime.py
PYTHONPATH=src python -m estate.cli.main engineering-provider-health collect --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0535 --json
```

## Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0535_codex_done.json
```

The receipt must include:

```text
work_package_id
status
providers_supported
health_states_implemented
files_created
files_modified
validation_commands_run
validation_results
live_provider_prompts_submitted
codex_polling_policy_respected
routing_health_integration_verified
office_consumption_verified
known_limitations
ready_for_ca_review
```

It must explicitly state:

```text
live_provider_prompts_submitted: false
codex_polling_policy_respected: true
```

## Out of Scope

Do not:

- create a new provider router;
- create a new capacity runtime;
- submit paid or quota-consuming prompts for health checks;
- enable automatic Codex polling when WP-0534 does not authorize it;
- dispatch work directly;
- grant authorization, validation acceptance, or institutional acceptance;
- create another Office dashboard when the existing Engineering Capacity surface can consume the data.

## Acceptance Criteria

1. A normalized provider-health runtime exists.
2. Initial Codex and local providers are represented.
3. Health states are deterministic and evidence-backed.
4. Polling obeys WP-0534 policy.
5. No prompt execution is used for health checks.
6. Current and historical artifacts are written.
7. Provider routing consumes health evidence.
8. Unhealthy providers are excluded from recommendations.
9. Degraded recommendations include explicit warnings.
10. Office consumers can render provider health without computing it.
11. Focused tests pass.
12. WP-0535 validation passes.
13. Completion receipt exists and is ready for Chief Architect review.

## Steward / Chief Architect Note

This package completes the provider evidence triad:

```text
Capability: What can the provider do?
Capacity: How much work can it accept?
Health: Is it operationally trustworthy right now?
```

The provider router may recommend dispatch only from combined evidence. Recommendations remain evidence, not decisions.
