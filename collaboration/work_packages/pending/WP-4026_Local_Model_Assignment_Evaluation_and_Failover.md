# WP-4026 — Local Model Assignment, Evaluation, and Failover

Status: Pending
Workstream Mode: PARALLEL-STAGED
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Stage per-resident local model assignment, evaluation, health inspection, and controlled failover without modifying active model-control, resident-chat, CLI, or Office files in this package.

## Conflict Surface

Expected integration targets:

- model-control registry, policy, and assignments;
- resident interaction adapters;
- AI-service controls;
- `src/estate/cli/main.py`;
- Office model and resident surfaces.

Conflict risk: high.

## Staged Paths

Use only `collaboration/workstreams/WP-4026/` for source, tests, fixtures, integration instructions, and `install_manifest.json`.

## Required Implementation

Stage:

- resident-to-model and capability-to-model assignments;
- local provider/model availability inspection;
- explicit fallback order;
- no-cloud policy enforcement;
- cold-start and timeout handling;
- assignment smoke tests;
- comparative evaluation records;
- model-change audit;
- truthful provider/model/fallback diagnostics;
- deterministic selection APIs.

## Boundaries

Do not create a second model registry, silently call cloud providers, auto-download models, or make evaluation scores self-authorizing. Preserve existing Estate model-control authority.

## Acceptance Criteria

- model selection is resident-aware and deterministic;
- failover never crosses prohibited provider boundaries;
- unavailable and cold-start states are truthful;
- model changes are auditable;
- staged tests pass;
- install manifest is complete and uninstalled.

## Required Install Handoff

WP-4031 installs model-control and resident-chat integrations in conflict order.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4026_Local_Model_Assignment_Evaluation_and_Failover.md and do exactly what it says.
```
