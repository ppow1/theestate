# GRC-MAIN-RECONCILE-001

## Result

The accepted Grace Cognition implementation was reconciled onto current
`ppow1/Riverview` `main` without merging the stale feature branch wholesale.

- Original main: `c29d6256e05bd0c98188a5113346cb3895f8259a`
- Old Grace feature HEAD: `3251993eadd11e0f9d867fde5aabbe1808113c80`
- Merge base: `bd3ff03d03887373cbfda59d633d90032206e95f`
- Divergence: feature 36 commits ahead, 89 commits behind main
- Final main: `475c955efb7985e03208162add6b4f01f886fef8`
- Remote verification: `origin/main` returned the same final SHA

No branch was created. The reconciliation was performed in a detached
worktree based on `origin/main`, then pushed with `HEAD:main` without force.

## Cause of divergence

Grace F1 through P3 work continued on
`codex/c484-operator-persistent-service` while Campaign Runner work continued
on `main`. The two lines consequently diverged. The feature line also carried
unrelated stale resident/operator/provider history, so it was not merged as a
whole.

## Grace implementation inventory

The following complete accepted Grace implementation chain was identified and
cherry-picked in dependency order. Validation reports were not imported into
Riverview.

| Package | Feature commit | Treatment |
| --- | --- | --- |
| F1 | `4e4d67c10cf956160d0478bf1b513f3a69383528` | selected |
| F1 repair | `c7646bb41ffbde51687a06023b0003e4679c8e3d` | selected |
| F1 aggregate repair | `4d58c5560b5d883ee5a39a690bed1459cd3524f2` | selected |
| F4 early assembler | `dab860cd8eb02b6333fbade67f6a63abb8887181` | selected |
| F2 | `2a04ce0b2977814baac4d8896467c92e1c3b9bfc` | selected |
| F2 correspondence repair | `005f953f63975ae83a1d61291ee1dbe9d80bf74a` | selected |
| F3 | `726b88755f8881fb283b5ac9a472290c6d33f37b` | selected |
| F4 identity/current-state repair | `15f6ae7734dade8400c289b799641876a1993aa1` | selected |
| F4 semantic-empty repair | `4f41dc4f765fa95babc1342ae63d05d049f402e3` | selected |
| P1 | `62b6ce0c5b51ff22e7ac2adf46d822b5fda03619` | selected |
| P2 | `5fbb36625e564fab7a9a53650a7005f30c08d500` | selected |
| P1 arbitrary-request repair | `f0ffa4ec78fc81b821b4f7948cc69066729dc147` | selected |
| P1 packet/classification repair | `82b515b63031b69fb790203e60da3b7a2ec823ed` | selected |
| P3 | `3251993eadd11e0f9d867fde5aabbe1808113c80` | selected; independently accepted by GRC-011V |

Unrelated feature-line commits, including C463-C484 resident/operator/provider
history and validation/report commits, were intentionally excluded.

## Integration dependency and method

The Grace chain cherry-picked cleanly onto current main; no source conflicts
were encountered. Initial collection exposed that current main did not contain
the accepted F4 assembler's required resident context support. The smallest
safe integration was to add only these required support artifacts from the
feature's accepted resident continuity implementation:

- `src/riverview/residents/context.py`
- `src/riverview/residents/persistence.py`
- `tests/test_resident_context.py`
- `database/migrations/0041_resident_continuity.sql`

The feature's resident schema was originally numbered 0035, but current main
already owns migration 0035. It was added as migration 0041 and the persistence
health check was aligned to 0041. The migration is idempotent for the shared
database's already-present resident tables and indexes. This preserved current
main migrations 0035 through 0040 and did not import stale feature history.

The reconciliation commit was `475c955efb7985e03208162add6b4f01f886fef8`.

## Verification

Grace validation on the reconciled tree:

- 128 focused tests passed across F1, F2, F3, F4, P1, P2, P3, resident context,
  provenance repairs, and packet repairs.
- `compileall` passed.
- Migration 0041 applied successfully to PostgreSQL.
- `ResidentContinuityStore.health()` reported `healthy`.
- P3 was treated as accepted based on GRC-011V commit
  `f6f77df2579f35aa2694a1b2b01bd24974afcaa2`.

Campaign Runner regression:

- Campaign Runner source and accepted symbols remained present, including
  `CampaignOneGoRunner`, `CampaignLifecycleStore`, `RelayStore`, and the
  transaction-scoped reconciliation authority.
- Relevant non-contaminated Campaign Runner tests remained executable.
- PostgreSQL Campaign Runner failures reproduced the known shared-database
  accumulated-expired-row contamination pattern; no Grace code touched those
  paths and no new Grace-related Campaign Runner failure was observed.
- Full collection was blocked by the pre-existing optional `mcp` dependency
  missing from the environment (`mcp.server.fastmcp`), unrelated to this
  reconciliation.

## Final component status

The final main tree contains:

- Grace F1: PRESENT
- Grace F2: PRESENT
- Grace F3: PRESENT
- Grace F4: PRESENT
- Grace P1: PRESENT
- Grace P2: PRESENT
- Grace P3: PRESENT
- Accepted Campaign Runner implementation: PRESENT

The old feature branch remains undeleted and unchanged at
`3251993eadd11e0f9d867fde5aabbe1808113c80`. It is now historical only; no
further development should occur there.

E1 was not started. The reconciliation start gate is ready to be rerun from
current `main`.
