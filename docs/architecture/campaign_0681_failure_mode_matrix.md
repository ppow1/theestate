# CAMPAIGN-0681 failure-mode matrix

WP-0705 validates the integrated operational model without adding a production
control plane. The executable matrix is
`tests/test_campaign_0681_failure_modes.py`.

| Domain | Injected condition | Required result | Canonical evidence seam |
|---|---|---|---|
| Services/residents | degraded, failed, blocked, stale projection | safe idle or escalation; no adapter call | health projections and momentum cycle record |
| Validation/readiness | missing and equally authoritative conflict | unverified/indeterminate; never ready or accepted | readiness evidence lineage |
| Policy/authority | conflicting office policy and protected deployment | escalation; no progression | guardrail audit record |
| Retry/control | exhausted budget plus acceptance blocker | attributable refusal; no dispatch | operational control evaluation |
| Interruption/repository state | interrupted durable checkpoint with completed side effect | replay skips completed work and reconstructs review state | existing runtime checkpoint/event/replay seam |
| Mailbox | stale repository message | route refused; no canonical message written | Alfred route evaluation |
| Steward visibility/privacy | degraded restricted service | degradation visible, details redacted, evidence linked | existing Steward dashboard projection |

Additional package and gate tests exercise malformed, duplicate, inaccessible,
future, superseded, and missing evidence; protected decisions; missing adapters;
missing outcome evidence; correction history; and closeout blocking.

Residual risks: the suite is deterministic repository-level validation, not a
production outage exercise. Runtime/provider availability and long-duration
freshness behavior remain observable operational risks. The corrective response is
to preserve safe idle, current health evidence, bounded retry, and protected human
review rather than weaken the gates.
