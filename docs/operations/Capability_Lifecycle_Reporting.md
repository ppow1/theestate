# Capability Lifecycle Reporting

Status: Operational Documentation
Classification: Estate Internal

## Purpose

Capability lifecycle reporting provides an operational validation layer over existing Estate capability registries and evidence artifacts. It helps Alfred, Audit, the Operations Board, and Chief Architects see which capabilities exist, which lifecycle states are valid, and where evidence is missing.

This report does not redefine the official Estate Capability Lifecycle States and is not a governance source of truth. The official lifecycle states remain those documented in `docs/governance/Capability_Lifecycle_States_v1.md`.

## Inputs Consumed

The reporter uses artifacts when present and records missing optional artifacts as warnings:

- `data/registry/capabilities.json`
- `data/registry/services.json`
- `docs/governance/Capability_Lifecycle_States_v1.md`
- `runtime/operations/operations_board.json`
- `runtime/audit/latest.json`
- `collaboration/audit/results/*.json`
- `docs/collaboration/*.md`

Malformed JSON is recorded as a warning and does not stop report generation.

## Outputs Generated

Running the report writes:

- `runtime/capabilities/capability_lifecycle_report.json`
- `operations/capabilities/lifecycle_status.md`

The Markdown output is a readable operational report for review. It should not be treated as a governance source of truth.

## CLI Usage

Print a concise summary and write both report files:

```bash
python -m estate.cli.main capability-lifecycle
```

Print the JSON report and write both report files:

```bash
python -m estate.cli.main capability-lifecycle --json
```

## Validation Rules

The reporter validates each capability for:

- stable capability identifier
- human-readable title or name
- lifecycle state
- owner or responsible office if present
- evidence references if maturity is above `Designed`
- implementation references if state is `Implemented` or higher
- operational evidence if state is `Operationally Validated` or higher
- institutional reference if state is `Institutionalized`

Only these lifecycle states are valid:

- `Designed`
- `Implemented`
- `Operationally Validated`
- `Institutionalized`

## Known Limitations

- The tool validates references as declared registry values; it does not prove that every referenced artifact is semantically sufficient evidence.
- Candidate lists are operational review aids, not automatic promotion decisions.
- Optional local runtime artifacts may be unavailable outside the Steward's local runtime and are reported as warnings rather than failures.
