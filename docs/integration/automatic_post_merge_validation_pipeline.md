# Automatic Post-Merge Validation Pipeline

The automatic post-merge validation pipeline closes the local merge-to-verdict loop without granting institutional acceptance authority.

## Flow

1. A pending post-merge audit request is written under `runtime/post_merge_audit/requests`.
2. `PostMergeAuditProcessor` claims exactly one `pending` request and moves it to `claimed`/`running_validation`.
3. `PostMergeValidationPipeline` copies the target repository to a dedicated validation workspace under the configured audit workspace root.
4. The active development tree is only inspected. Dirtiness is reported as `active_tree_dirty_reported_not_repaired`; the pipeline never stashes or repairs it.
5. The pipeline verifies the target base branch, expected revision metadata, and expected files.
6. The standard validator is invoked as `python -m estate.cli.main validate-work-package --id <WP-ID> --json` from the clean workspace.
7. Completion receipt status and production readiness are read using the existing production-readiness helpers.
8. A Ring 2 prompt is always generated under the external evidence root.
9. Ollama review is disabled by default and only runs when the processor/runtime explicitly enables Ring 2 execution.
10. A bounded verdict artifact is written and the request/status summaries are updated for Office visibility.

## Boundaries

The pipeline does not execute providers, execute dispatch work, merge code, commit repairs, or create Chief Architect / Steward acceptance. Verdicts such as `ring2_required`, `accepted_with_notes`, or `needs_repair` are evidence only.

## CLI

```powershell
python -m estate.cli.main post-merge-audit process-next --json
python -m estate.cli.main post-merge-audit process-all --max 10 --json
python -m estate.cli.main post-merge-audit demonstrate --work-package WP-0620 --pr 199 --json
python -m estate.cli.main operations-runtime run-once --process-audits --json
python -m estate.cli.main operations-runtime start --process-audits --max-cycles 10 --interval-seconds 30 --json
```

## Office / Background Status

The Office status bar consumes `runtime/post_merge_audit/status/latest.json` and exposes automatic validation availability, pending/running/latest audit details, latest validation/production/Ring 2/verdict state, workspace health, and evidence root.
