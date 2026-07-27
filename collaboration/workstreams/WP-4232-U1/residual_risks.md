# Residual risks

- The final WP-4232 bounded-live acceptance input remains separately gated and
  was not executed.
- The provider adapter is intentionally limited to the deterministic SHA-256
  test effect; no general provider admission is implied.
- Local Windows pytest ACLs require an external writable basetemp and disabled
  bytecode/cache for reproducible test execution.
