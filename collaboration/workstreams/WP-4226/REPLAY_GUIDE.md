# Replay guide

1. Assemble a JSON object with the exact keys `engineering_queue`, `dashboard`, `integration`,
   `recommendations`, `decision_ledger`, and `analytics`. Values must be the already-published
   outputs; do not invoke their generators.
2. Supply a stable UTC generation time to `snapshot`. Identical inputs and time yield identical
   identifiers, bytes, and hashes.
3. Run `validate` before diagnostics. Unsupported schemas, malformed source sets, tampering,
   and provenance drift fail closed with a non-zero exit.
4. Run `replay` to retrieve captured views, or `compare` for a declarative historical delta.
   A changed priority is reported from the records and is never scored again.
5. Use `explain` to trace every source hash. Preserve the source bundle outside authoritative
   repository locations if an operator elects to archive CLI output.

The framework is intentionally incapable of executing advice, altering lifecycle state,
writing Git, or assigning, scheduling, and dispatching workers.
