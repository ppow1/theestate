# Estate Audit Standard
Version: 0.1
Status: Draft
Owner: Archives / Engineering

Purpose:
Estate Audit protects institutional continuity by comparing declared history, runtime state, and Git history.

Initial audit checks:
- Python syntax validation
- CLI runtime validation
- Git working tree status
- Latest commit EC number
- Latest ledger EC number
- EC drift detection
- Registry readability
- Observation readability

Rule:
A committed repair must preserve the broken historical record and add a new corrective Estate Change.
