# Merge Gate

This draft is not merge-ready.

The reviewed patch artifacts are now both preserved on the branch:

- `0001-repair-message-boundaries.patch`
- `0002-segment-runtime-canons.patch`

Required before merge:

- apply both patches to repository source and focused tests;
- run the focused ingestion and runtime-canon recovery tests;
- run the private five-archive acceptance suite;
- confirm 102 total messages and 25 assistant messages;
- confirm WP-4111 and WP-4112 matching explicit closures;
- confirm WP-0026 quoted/startup-seed rejection;
- confirm byte-identical deterministic reruns;
- keep recovered bodies and source archives out of Git.
