# WP-4231 contract assumptions

WP-4231 consumes `estate.grace-momentum-client.v1` exclusively through
`GraceMomentumClient`. The temporary local binding is `FakeGraceMomentumService`
for component and browser-shell testing; production network transport binding is
explicitly deferred.

## Assumptions applied

- Query names and event records are the authoritative display source. No Estate
  runtime persistence path is read by the adapter.
- Every mutation uses `GraceMomentumClient.send()` with a caller supplied or
  generated idempotency key. The UI does not retry a new key for the same intent.
- The contract's canonical deep-link templates are used verbatim with URL-encoded
  identifiers. Links are navigation only.
- Provider effects remain suppressed in fixture, shadow, and bounded-live modes.
- Recovery is limited to `replay.state` inspection and `progression.inspect`.
  No rerun control is rendered.

## Published-contract gaps

- `grace_momentum_control_contract.v1.json` was requested but is not present in
  shared commit `2a3afce68f3527540d4c0b2f7083eb31aed9e4c6` or its worktree.
- `GraceMomentumClient` exposes no subscription method. The UI therefore derives
  incremental events from the contract's `lifecycle.timeline` query and cursor;
  it does not reach through to the service. A client subscription method is needed
  for real push updates.
- The contract has no control-availability query. Controls are labelled
  `server_authority_checked_on_submit`, and authority denial is surfaced from the
  client rather than inferred locally.
- The contract does not yet project distinct Helen, commission, provider,
  Dispatch, reconciliation, validation, receipt, or diagnostic fields. WP-4231
  renders their canonical query categories without inventing values; richer
  field-level cards require a compatible query projection from WP-4229.
