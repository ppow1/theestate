# WP-0692 conflict and reuse report

The implementation reuses the CAMPAIGN-0681 execution manifest as the source of
campaign topology and package identity, manifest-declared completion receipts
as bounded implementation evidence, Git as repository identity, and the
read-only projection pattern used by the health-signal integration.

It does not extend the mutable `OperationalCampaignRuntime`, because that seam
can dispatch and mutate campaign state. It does not create a status database,
queue, event log, dashboard registry, acceptance record, or implicit dependency
graph. Existing PTM, Dispatch, readiness, validation, evidence, health,
mailbox, office, and protected-acceptance systems remain authoritative.

The older operational campaign model uses a different runtime campaign shape;
the observer deliberately consumes the canonical execution manifest rather than
claiming that the runtime model supersedes repository campaign definitions.
