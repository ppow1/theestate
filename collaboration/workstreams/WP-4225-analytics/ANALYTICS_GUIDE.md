# Analytics guide

Each observation must contain `observed_at` and exactly five `sources`: `queue`, `dashboard`, `integration`, `recommendations`, and `decision_ledger`. These are published values, identified by their existing deterministic hashes. Analytics never repairs, infers replacements for, or writes these records.

Recommendation rates use the latest published ledger state. Aging measures generation-to-latest-decision (or observation time). Execution measurements count only explicit published fields: completed/merged state, passed/complete validation, blockers, dependency edges, stale diagnostics, lanes, high merge risk, and technical-debt classification. A missing denominator produces zero rather than an invented estimate. Confidence and freshness describe the observation snapshot, not operational readiness.

Daily, weekly, and monthly reports use inclusive trailing 1-, 7-, and 30-day windows ending at the latest supplied snapshot. Campaign-lifetime reports include all supplied snapshots. Comparisons subtract left metric values from right values and retain both hashes as provenance. Reports describe changes; they never label work as preferable or alter priority.
