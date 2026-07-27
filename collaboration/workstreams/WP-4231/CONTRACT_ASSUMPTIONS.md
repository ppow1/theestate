# WP-4231 contract assumptions

WP-4231 consumes merged WP-4229 contract `0fcb07b55cedc74d1b2dffe67f8218d3bcffc08c`
exclusively through `LoopbackGraceMomentumClient`. `FakeGraceMomentumService` is
used only by explicit component/contract-test fixtures.

## Assumptions applied

- `replay()`, `subscribe()`, `availability()`, and `lifecycle_projection()` are
  the authoritative display source. No Estate runtime persistence path is read.
- Every mutation uses `GraceMomentumClient.send()` with a caller supplied or
  generated idempotency key. The UI does not retry a new key for the same intent.
- The contract's canonical deep-link templates are used verbatim with URL-encoded
  identifiers. Links are navigation only.
- Provider effects remain suppressed in fixture, shadow, and bounded-live modes.
- Recovery is limited to `replay.state` inspection and `progression.inspect`.
  No rerun control is rendered.

## Remaining contract/runtime gaps

- Provider deployment and transport availability remain environment concerns;
  unavailable/malformed loopback responses fail closed.
- WP-4231 renders provider projection fields and does not derive lifecycle state.
