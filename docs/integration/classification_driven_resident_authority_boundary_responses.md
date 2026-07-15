# Classification-Driven Resident Authority Boundary Responses

Resident authority checks now emit a `classification_driven_response` object in addition to the underlying allow/deny decision. The response object is derived from the resident action authority classification and exists only to guide the operator-facing wording and next step.

## Purpose

The resident boundary already decides whether a requested action is allowed, denied, requires Steward approval, or requires escalation. Classification-driven responses make that decision easier to render consistently in resident conversations, duty summaries, and operational surfaces without granting new authority.

## Response Contract

Each `check_authority(...)` result includes:

- `response_classification` — the authority classification that drove the response.
- `boundary_response` — human-readable response label such as `Allowed`, `Denied`, `Requires Steward approval`, or `Requires escalation`.
- `response_tone` — presentation guidance for downstream surfaces.
- `operator_message` — concise status text for operators.
- `resident_instruction` — safe resident-facing instruction for how to respond.
- `must_not_execute` — `true` for denied, approval-required, and escalation-required outcomes.
- `reason` — the same boundary reason attached to the authority decision.

## Authority Boundary

The response contract does not change the source-of-truth authority decision. Denied, approval-required, and escalation-required actions remain blocked for residents. Allowed actions remain non-authoritative resident activity unless another Estate authority explicitly grants more.

## Example Command

```bash
PYTHONPATH=src python -m estate.cli.main resident-authority check --resident Alfred --action execute-work-package --target WP-0633 --json
```

The resulting JSON includes `classification_driven_response.must_not_execute=true`, preserving the execution boundary while providing consistent wording for resident and Office surfaces.
