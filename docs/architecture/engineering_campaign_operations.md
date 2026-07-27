# Engineering Campaign Operations Architecture

The WP-4228 composition layer converts accepted, current Engineering recommendations into proposed institutional records without bypassing Grace, Helen, Engineering, or Dispatch. It uses deterministic hashes/IDs, append-only hash chaining, explicit action classification, and retry-safe idempotency. It is neither a scheduler nor an execution provider. See `collaboration/workstreams/WP-4228/PRODUCTION_ARCHITECTURE.md` for the full boundary.
