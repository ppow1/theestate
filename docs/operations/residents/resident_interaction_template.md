# Resident Interaction Template

Use the resident interaction service for local Operations Center chat requests:

1. Resolve resident surface and versions.
2. Discover local LLM provider; use deterministic fallback only when unavailable or in tests.
3. Attach authority metadata before any response claims action status.
4. Persist every turn under `runtime/resident_interactions/sessions`.
5. Use Steward forget/redaction commands to suppress content while preserving audit fact.
6. Surface extensions must be proposed through the resident API extension proposal template.

Local endpoints: `GET /api/residents/{resident_id}/surface`, `GET/POST /api/residents/{resident_id}/chat`, and `POST /api/residents/{resident_id}/forget`.
