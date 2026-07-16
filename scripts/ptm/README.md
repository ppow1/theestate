# Estate PTM repository verification toolkit

`Test-EstatePtmRepository.ps1` is the canonical, repository-maintained, read-only
verification command for the completed Estate Project Task Management (PTM)
planning and package-execution sprint.

## Run

From the repository root in Windows PowerShell 5.1 or PowerShell 7:

```powershell
CLS
& .\scripts\ptm\Test-EstatePtmRepository.ps1
```

The command exits `0` only when all required checks pass. For automation, request
the stable JSON result envelope:

```powershell
CLS
& .\scripts\ptm\Test-EstatePtmRepository.ps1 -Json |
    Set-Content -Encoding UTF8 .\ptm-verification.json
```

Use `-RepositoryRoot` to inspect another checkout. During an authorized campaign
that has not yet produced receipts, `-SkipCompletionReceipts` checks the planning
graph without claiming that execution is complete.

## Verification scope

The toolkit checks:

- valid, present package, campaign, and dependency manifests;
- unique package and campaign identities;
- repository-relative paths that cannot escape the checkout;
- existence of pending packages, source drafts, campaign instructions, and other
  manifest-referenced files;
- one-to-one package/campaign membership and campaign consistency;
- exact agreement between package and hard-dependency declarations;
- known dependency targets and an acyclic dependency graph;
- the accepted Codex-only execution-lane assignment; and
- one completion receipt for each Codex-routed package after campaign completion.

The verifier does **not** mutate package state, infer governance acceptance, create
a queue or registry, or replace the source manifests. Findings identify the
source artifact to review; the authoritative record remains in its existing
repository location.

## Read-only adapter contract fixtures

From the repository root, run the Gate G2 fixture integration checks with:

```text
pytest -q tests/test_ptm_read_only_adapter_contract_fixtures.py
```

The expected result is `4 passed`. The command exercises sanitized Parking Lot,
work-package, Dispatch, validation, and acceptance shapes and must leave the
fixture sandbox byte-for-byte, timestamp-for-timestamp, and mode-for-mode
unchanged. It also expects missing and oversized records to be unavailable,
conflicting status to remain explicit, stale records to be marked stale, path
escapes to fail closed, source hashes to be calculated from bytes, and explicitly
private fields to be absent from normalized results. The fixtures under
`tests/fixtures/ptm_read_only_adapters/` are non-production test inputs, never an
authoritative dataset.
