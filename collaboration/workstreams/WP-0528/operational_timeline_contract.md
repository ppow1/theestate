# WP-0528 Operational Timeline Contract

This staged contract defines a read-only, unified operational timeline for the Estate Office. The staged implementation is not installed work and does not modify shared active Office files.

## Purpose

The timeline normalizes existing merges, validations, decisions, resident duties, Office actions, provider results, and operational events into chronological entries. It is an index and correlation surface only; canonical source artifacts remain authoritative.

## Entry Shape

Each normalized event exposes:

- `id`: stable event identifier from the source adapter.
- `occurred_at`: ISO-8601 timestamp used for deterministic ordering.
- `event_type`: one of `merge`, `validation`, `decision`, `resident_duty`, `office_action`, `provider_result`, or `operational_event`.
- `source.type`: source class such as git merge, validation result, decision record, duty roster, or provider output.
- `source.evidence_path`: repository-relative evidence path.
- `actor`, `package`, `project`, `office`, and `outcome`: filterable operational dimensions.
- `correlation_id`: optional relationship key that links related events without rewriting the source event.
- `canonical_artifact`: drill-down target, defaulting to the evidence path.
- `indicators`: freshness, gap, duplicate, missing evidence, and malformed evidence status.

## Filtering

The timeline supports filters by:

- date range (`date_from`, `date_to`);
- actor;
- package;
- project;
- office;
- event type;
- outcome.

Filters are applied to normalized timeline entries and never mutate source artifacts.

## Correlation

Correlation groups are derived from `correlation_id`, falling back to package, project, or event id. Correlation links related events for navigation and analysis only; they do not rewrite canonical history or create a competing event source.

## Export

Filtered or complete timelines can be exported as JSON or CSV. Exports include source links so operators can drill down to canonical artifacts.

## Installation Boundary

WP-0531 owns installation into active Office modules, workspace registration, and adapter wiring. This workstream is staged only.
