# Continuous Operational Validation Reporting

Status: Implemented reporting support  
Classification: Estate Internal

## Purpose

The continuous operational validation reporter summarizes evidence that may support lifecycle review for Estate capabilities. It reports candidates and gaps only. It does not promote capabilities, change lifecycle state, create lifecycle states, or redefine operational validation.

## Inputs

The reporter uses these artifacts when present:

- `runtime/capabilities/capability_lifecycle_report.json`
- `runtime/operations/operations_board.json`
- `runtime/audit/latest.json`
- `collaboration/audit/results/*.json`
- `runtime/collaboration/events/events.jsonl`
- `collaboration/status/worker_inbox_summary.json`
- `operations/**/*.md`

Missing inputs are recorded as warnings and missing inputs. They are not fatal errors.

## Outputs

The reporter writes:

- `runtime/validation/operational_validation_report.json`
- `operations/validation/operational_validation_report.md`

## CLI Usage

```bash
python -m estate.cli.main operational-validation
python -m estate.cli.main operational-validation --json
```

## Evidence Rules

- Implementation references from the lifecycle report count as implementation evidence.
- Lifecycle evidence references count as validation evidence.
- Runtime operations board data, audit artifacts, collaboration event data, worker inbox summaries, and operations Markdown mentions count as validation evidence when they identify the capability by id or name.
- Existing operational evidence references are required for completeness when a capability already claims `Operationally Validated` or `Institutionalized`.
- Institutionalized claims also require institutionalization references to avoid reporting a complete evidence set without adoption evidence.

## Candidate Rules

- A capability in `Implemented` state with implementation evidence and validation evidence, and no evidence gaps, is reported as a candidate for `Operationally Validated` review.
- A capability in `Operationally Validated` state with continuing validation evidence is reported as a candidate for `Institutionalized` review.
- Candidate status is advisory only. Lifecycle promotion remains a governance/review decision.

## Relationship to Capability Lifecycle States

This reporter consumes the lifecycle states defined in `docs/governance/Capability_Lifecycle_States_v1.md`: `Designed`, `Implemented`, `Operationally Validated`, and `Institutionalized`. It does not create new states or change governance meaning.

## Limitations

- The report is evidence-oriented, not authoritative governance approval.
- Text evidence is matched by capability id or name, so ambiguous names may require human review.
- Missing and malformed artifacts reduce evidence confidence but do not stop report generation.
- The tool never modifies capability lifecycle state automatically.
