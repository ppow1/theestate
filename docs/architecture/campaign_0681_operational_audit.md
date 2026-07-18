# CAMPAIGN-0681 operational audit and explainability

WP-0702 extends the existing append-only autonomous operations JSONL audit. It
does not create a competing audit store. Operational events distinguish observed
facts, derived state, recommendations, policy decisions, authorizations, actions,
escalations, and corrections.

Each event has stable identity; campaign, package, office/resident/service, cycle,
recommendation, and action correlations as applicable; canonical source evidence;
freshness; confidence; policy disposition; authority references; outcome;
uncertainty; classification; and correction/supersession links.

Corrections append a new record and must reference an existing event. Original
records remain intact. Duplicate identities and orphan corrections are refused.
Restricted or personal payloads remain in their authorized canonical stores; the
audit contains references only.

Queries reconstruct ordered histories by correlation and keep corrected,
superseded, missing, stale, partial, and conflicting evidence visible. Generated
Markdown explanations are explicitly non-authoritative and always link back to
canonical evidence. Retention follows the existing audit JSONL policy; records
are not erased or rewritten by this adapter.
