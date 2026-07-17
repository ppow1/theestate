# WP-0691 conflict and reuse report

## Canonical seams extended or consumed

| Domain | Canonical seam | WP-0691 treatment |
|---|---|---|
| Service health | `src/estate/core/service_health_registry.py` | Consumes health entries and authoritative source links; no writes or probing. |
| Service board/dependencies | `src/estate/core/service_status_board.py` and dependency summaries | Consumes display/dependency context without making the board authoritative. |
| Resident lifecycle | `src/estate/core/resident_lifecycle.py` | Maps lifecycle records; does not call transitions. |
| Resident interaction | `src/estate/core/resident_interaction.py` | May qualify a signal, but responsiveness never proves readiness. |
| Worker runtime | `src/estate/core/worker_runtime_heartbeat.py` | Maps reported heartbeat and its expiry; no heartbeat creation. |
| Operations runtime | `src/estate/core/operations_runtime.py` | Maps completed-cycle/readiness evidence; process existence alone is insufficient. |
| Provider/environment | Existing Engineering provider-health evidence | Bounded adapter only; no new provider registry. |
| Validation | `src/estate/core/work_package_validation.py` and schema-valid reports | Maps verdict evidence independently of acceptance. |
| Steward visibility | `src/estate/core/steward_command_center.py` | Output is suitable for later consumption; WP-0691 adds no command or authority. |
| Campaign model | CAMPAIGN-0681 and WP-0689 required contract | Uses canonical identities, evidence references, bounded states, and observation/action separation. |

## Duplicate systems deliberately avoided

WP-0691 creates no persistent database, registry, queue, scheduler, mailbox,
message transport, dashboard, campaign-state store, provider registry,
validator, office, or acceptance mechanism. The new module is a pure bounded
normalization adapter. It does not write runtime state.

## Discovery conflicts and qualifications

The checkout contains the WP-0688 and WP-0689 specifications but no completion
receipts or accepted deliverables for those packages. Their required contract
language is therefore reused as a repository-integrated specification, not
represented as completed or protected-accepted. The CAMPAIGN-0681 bounded reuse
record also states CAMPAIGN-0670 is not accepted; no source from that lineage is
described as accepted here. These are explicit review qualifications for the
Chief Architect and do not permit invention of a replacement operational state
store.

Canonical source timestamps are heterogeneous and sometimes absent. Missing
timestamps produce unknown freshness and a warning; expired timestamps produce
`stale`. Canonical dependency-to-campaign relationships are accepted only when
provided by the caller/source record, so unrelated work is not blocked by
inference.
