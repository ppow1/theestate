# Fixture and shadow evidence

The existing real-runtime fixture and shadow evidence remains at
`../WP-4232/acceptance_evidence.json`. U1 preserves those modes: provider
effects remain suppressed unless the explicit `governed_local_test` mode is
selected and the provider-admission readiness gate is satisfied.

The U1 lifecycle evidence in `acceptance_evidence.json` is a distinct local
deterministic test-provider run and does not claim final WP-4232 bounded-live
acceptance.
