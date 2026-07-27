# Architecture

The framework is a pure projection: published JSON enters `assess`, structural
and version checks fail closed, and a new advisory report leaves the process.
Inputs are deep-copied and only inspected. Per-recommendation evidence bundles
retain hashes for every upstream publication and exact source references.
Evidence summaries expose every rule result, missing/conflicting evidence,
degraded provider identifiers, and published freshness state.

The confidence hash covers the complete assessment except itself. The report
hash covers metadata and every assessment. Validation recalculates both. This
makes repeated runs and tampering observable without granting the framework any
authority. Comparison and history compare reports; they do not infer upstream
state or modify recommendation order.
