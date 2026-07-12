# Resident Presence and Estate Culture Runtime v1

This runtime implements Campaign 05 (WP-4083 through WP-4092) as a governed projection layer. It reads canonical resident registry, runtime presence, visual location, historical archive, relationship, and culture artifacts and returns source-lined presentation records.

## Architectural boundaries

- It does not create a second scheduler, calendar, message bus, relationship graph, memory store, gallery, archive, governance body, security tracker, or personnel system.
- Ambient activities and environmental details are presentation records unless backed by durable evidence.
- Passive interactions are transient and cannot create tasks, approvals, messages, relationship state, commitments, or institutional facts.
- Presence API responses are read-only and expose uncertainty, freshness, confidence, source class, simulation state, and diagnostics.
- Traditions, annual events, running jokes, shared cultural memory, and culture evolution remain source-lined and review-governed.

## Implemented work packages

1. WP-4083: ambient resident activity records and lifecycle projection.
2. WP-4084: dynamic occupancy records, room summaries, freshness, and conflict diagnostics.
3. WP-4085: bounded passive interaction generation from co-location.
4. WP-4086: environmental details derived from visible occupancy.
5. WP-4087: read-only resident presence API response.
6. WP-4088: source-lined tradition registry projection.
7. WP-4089: shared institutional culture-memory projection.
8. WP-4090: consent-aware running joke and friendly rivalry controls.
9. WP-4091: annual event templates separating plans from attendance evidence.
10. WP-4092: culture signals and change proposals requiring explicit review.

## Runtime validation

Use `validate_presence_culture_runtime` to verify privacy, authority, source-lineage, and contradiction diagnostics. A valid runtime has zero error diagnostics and still reports warnings explicitly rather than hiding uncertainty.
