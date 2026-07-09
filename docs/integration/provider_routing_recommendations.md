# Provider Routing Recommendations

Status: Implemented for WP-0614  
Classification: Estate Internal

## Purpose

The provider routing recommendation layer produces deterministic provider-fit metadata for planned work. A recommendation is evidence for a Traffic Controller / Operations Manager decision; it is not a decision, schedule, dispatch, assignment, or provider execution.

## Allowed Recommendation Candidates

- `deterministic_local_tooling`
- `local_ollama_gpu`
- `chatgpt_planning`
- `codex_cloud_web`
- `codex_cli`
- `human_review`

## Runtime Artifacts

The runtime writer stores local evidence under:

```text
runtime/provider_routing/recommendations/<recommendation_id>.json
runtime/provider_routing/status/latest.json
runtime/provider_routing/status/summary.json
runtime/provider_routing/reports/<recommendation_id>.md
```

These artifacts are local runtime evidence and should not be treated as live provider execution logs.

## CLI Usage

Evaluate a JSON request and write runtime artifacts:

```bash
python -m estate.cli.main provider-routing-recommendation evaluate --request Temp/provider_routing_request.json --json
```

Explain a JSON request without live provider calls:

```bash
python -m estate.cli.main provider-routing-recommendation explain --request Temp/provider_routing_request.json
```

## Boundaries

The implementation does not call Codex CLI, ChatGPT, Ollama, GPUs, live network services, dispatch queues, or the Orchestrator runtime. It does not create a provider catalog, dispatch queue, event system, office, scheduling policy, or autonomous routing policy.
