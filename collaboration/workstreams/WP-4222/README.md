# WP-4222 staged Engineering Campaign Dashboard integration

This removable staging layer registers immutable local providers and composes the existing
WP-4221 dashboard projection over the existing WP-4220 queue.  It does not replace either
contract.  Optional WP-4214 duration, WP-4215 parallel-worker, and WP-4217 Git-readiness
artifacts are registered by version; their absence is an explicit degraded condition rather
than permission to invent values.

`dashboard_integration/integration.py` supplies deterministic provider discovery, exact-major
version negotiation, advertised-schema checks, snapshot loading/validation, panel discovery,
health diagnostics, and degradation reporting.  It verifies provider bytes before and after
each load.  Required provider failure is fail-closed.  The command writes only an explicitly
requested output file, atomically, and refuses output overlap with a provider.

Run the staged demonstration:

```bash
python collaboration/workstreams/WP-4222/integrate.py \
  collaboration/workstreams/WP-4222/fixtures/providers.json \
  --output /tmp/wp4222-integration.json
```

No package is added to `src`, no runtime route or scheduler imports this code, and no browser,
React, HTML, CSS, Open WebUI, Office, dispatch, lifecycle, Git, or network capability exists.
Rollback is deletion of this directory and the WP-4222 package artifact.  Installation is
not authorized; see `INSTALL_HANDOFF.md`.
