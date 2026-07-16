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
