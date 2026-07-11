# WP-4027 Integration Notes

This staged service remains uninstalled. WP-4031 may later install approved reporting and evidence-consumption integrations only.

## Consumption Contract

- Helen may consume `measured_evidence.sources`, dimension summaries, and categorical findings for review queues.
- No consumer should treat a score or category as institutional acceptance.
- Unsupported claims are reported under the `unsupported_claims` dimension and should not be merged into ordinary task quality defects.
- Boundary and identity issues are visible through `interpretation.boundary_failure_dimensions`.

## Non-Goals

- Do not diagnose residents.
- Do not impose workforce actions.
- Do not change model assignments or provider routing automatically.
- Do not require live model providers for validation.
