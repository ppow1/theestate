# Engineering Notebook Standard

The Engineering Notebook is a compact verified working-state projection for an
active bounded assignment. It answers: what job is active, what stage is next,
what scope is permitted, what evidence is current, and what blocks continuation.

## Authority

Repository canon, work packages, architecture, authorization, provider
readiness, receipts, validation results, and institutional records outrank the
notebook. A notebook can reference and summarize them; it cannot replace or
rewrite them. `institutional_acceptance` is permanently `not_granted` in this
layer.

## Two representations

Machine-readable JSON state is canonical for execution. Markdown is generated
for review, handoff, and bounded model injection. Markdown is never parsed as
authority. Every material claim carries a provenance category: worker proposal,
harness observation, validator result, operator authorization, or repository
fact.

## Contents

Identity, objective, stage state, scope, authority flags, protected interfaces,
validation evidence, source digests, blockers, repair limits, handoff reason,
omitted context, expiration, and conflict state are required. Secrets,
credentials, cookies, private prompts, unrestricted diffs, and chain-of-thought
are prohibited.

## Update rule

Workers propose bounded changes. The harness compares each proposal with actual
files, commands, receipts, and validators. Only observed, schema-valid changes
to task/evidence/continuity/status/freshness may be accepted. Identity,
authority, constraints, architecture, and institutional acceptance cannot be
worker-updated. Rejected proposals remain evidence; they are not silently
discarded.

## Freshness

Source commit, work-package, architecture, provider, authorization, validation,
and worker-assignment digests are checked before action. Changed digests produce
`conflicted`; age beyond the configured limit produces `stale`. Orientation from
a stale notebook is allowed, execution is not.
