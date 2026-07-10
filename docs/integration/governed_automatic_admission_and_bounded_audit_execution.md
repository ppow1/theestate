# Governed Automatic Admission and Bounded Audit Execution

WP-0625 adds automatic admission for current, receipt-backed canonical merge-discovery candidates and bounded consumption by Operations Runtime.

## Admission

`estate.core.merge_discovery_admission.MergeDiscoveryAdmission` classifies canonical candidates as current, historical backfill, manual hold, ambiguous, already audited, or superseded. Current candidates with target identity, work-package identity, receipt evidence, no final verdict, no hold, and no provider/dispatch execution evidence are admitted by creating a canonical post-merge audit request. Historical backfill remains quarantined unless explicitly released and reprocessed.

Commands:

```bash
python -m estate.cli.main merge-discovery admission-status --target estate-main --json
python -m estate.cli.main merge-discovery auto-admit --target estate-main --json
python -m estate.cli.main merge-discovery hold --target estate-main --work-package WP-XXXX --json
python -m estate.cli.main merge-discovery release --target estate-main --work-package WP-XXXX --json
```

## Bounded Runtime

Operations Runtime accepts `--max-audit-requests` and calls the audit processor with that maximum. The processor prefers canonical admitted requests, skips superseded or historical/quarantined requests, and marks requests already covered by final verdict evidence as `already_audited`.

```bash
python -m estate.cli.main operations-runtime run-once --discover-merges --auto-admit --process-audits --max-audit-requests 5 --json
```

## Ring 2 and Authority Boundary

Deterministic validation writes validation evidence and a Ring 2 prompt under the configured validation evidence root. When local Ollama review is not explicitly enabled the verdict remains `ring2_required`; this is review preparation, not institutional acceptance. Provider execution and dispatch execution remain false throughout the flow.
