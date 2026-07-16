# Estate PTM Schedule Validation Fixtures and Critical Path Plan

## Authority and scope

This validation artifact satisfies SCHED-PTM-001B for future validation fixtures. It depends on the schedule dependency and readiness-gate contract and preserves the frozen CORE-PTM-003B projection fields.

## Fixture set

Future schedule validation fixtures should include these deterministic cases:

| Fixture ID | Purpose | Minimum tasks | Expected result |
| --- | --- | ---: | --- |
| `sched_ready_linear` | Linear dependency chain with all gates passing | 3 | Last task ready only after predecessors complete; all critical-path flags true. |
| `sched_blocked_dependency` | Unsatisfied dependency | 2 | Dependent task readiness is blocked and blocked reason is `dependency`. |
| `sched_waived_dependency` | Chief Architect waiver | 2 | Dependency remains visible with `satisfaction_state=waived`; readiness may pass if all other gates pass. |
| `sched_unknown_estimate` | Missing estimate | 1 | Unknown duration remains null and emits warning; no false precision. |
| `sched_parallel_paths` | Two paths with different durations | 5 | Longest duration path is critical; shorter branch is not. |
| `sched_blocked_interval_overlap` | Multiple blocker reasons | 1 | Overlapping intervals are preserved and summarized by reason. |
| `sched_gate_unknown` | Non-waived unknown gate | 1 | Readiness state remains `unknown` and dispatch-ready publication is blocked. |

## Fixture record shape

```yaml
schedule_validation_fixture:
  fixture_id: string
  description: string
  input_events: [object]
  expected_schedule_records: [object]
  expected_readiness_states: [object]
  expected_critical_path: [string]
  expected_warnings: [string]
```

Fixtures should be stable replay inputs. They must use canonical event references or mock event records clearly labeled as fixture data.

## Critical-path calculation plan

1. Build a directed acyclic dependency graph from schedule records where edges represent blocking dependencies.
2. Validate that cycles fail closed with a warning and no critical-path publication for the affected subgraph.
3. Weight each node by active execution, validation, expected rework, integration, known queue/review wait, and known blocked dependency wait.
4. Calculate earliest start and finish by topological order.
5. Calculate latest start and finish by reverse topological order.
6. Mark records with zero slack on the longest valid path as `critical_path_flag=true`.
7. Preserve unknown estimates as unknown; if a path contains unknown duration, mark affected critical-path result as `unknown` rather than manufacturing a value.

## Validation assertions

- Gate failures prevent ready publication unless explicitly waived.
- Waivers preserve evidence references.
- Minute fields remain separated by duration type.
- No fixture introduces a runtime scheduler, dispatch queue, registry, or governance authority.

- No production PTM code is authorized by this contract.
