# WP-4232 Checksum Manifest

This is the checksum control record for the documentation package. It is not
a checksum of an external Git bundle or evidence archive; those artifacts
were not authorized or created.

| Artifact | State |
|---|---|
| Git bundle | not created; authorization and retention root absent |
| non-Git evidence archive | not created; authorization and retention root absent |
| source-path manifest | recorded in `ESTATE-OPS-002_WP4232_NonGit_Evidence_Manifest_20260802.md`; full re-capture required before retirement |
| local Git configuration capture | inspected read-only from `A:\theestate\.git\config`; not copied into Git |
| worktree registration | inspected read-only; registration remains active |
| shared stash inventory | 16 entries observed; no entry changed |

Before separate retirement authorization, generate SHA-256 values for the
bundle, archive, every manifest, and the restoration-test output, then verify
them from a second isolated location. Do not place large binary artifacts in
Git.
