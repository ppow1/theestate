# Automatic Validation Reconciliation and Queue Drain

WP-0639 adds a canonical reconciliation service and CLI for rebuilding a ledger from merge-discovery candidates, audit requests, validation evidence, and verdicts. Runtime draining delegates to the existing post-merge audit processor and reports bounded-cycle capacity, throughput, backlog, and zero-throughput reasons. Mutable background extension configuration is generated under ignored runtime state instead of committed `config/` paths.
