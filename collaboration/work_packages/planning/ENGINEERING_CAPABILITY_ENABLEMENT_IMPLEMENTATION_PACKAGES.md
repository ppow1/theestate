# Engineering Capability Enablement Implementation Packages

Status: Authored implementation decomposition; package IDs remain governed by
the existing campaign owners.

## Ownership reconciliation

| Implementation slice | Existing package owner | This branch's role |
|---|---|---|
| Inquiry, assessment, gap, and worker specification | WP-0695 with WP-0671 intake contract | Adds a correlation-first runtime seam without replacing Helen or Grace records. |
| Enabling dependency and resumption | WP-0671 readiness/dependencies with WP-0697 projection | Uses Grace objective state and existing PTM/orchestrator dependency ownership. |
| Provider registration and adapter contract | WP-0604 and WP-0613; WP-0672 Gate-B routing | Extends the existing catalog/adapter seam and preserves the Gate-B authority boundary. |
| Codex CLI adapter | WP-0672 execution lane, after registration evidence | Implements only bounded `codex.execution.cli`; no merge or institutional acceptance. |
| Validation and acceptance | WP-0673 and existing Chief Architect/Steward gates | Adds tests and local evidence; does not claim protected acceptance. |

No new registry, scheduler, Dispatch queue, or acceptance authority is created.
The existing pending package documents remain the governing specifications and
must be amended or superseded by their owners if these contracts are promoted.

## Dependency order

```text
contract ownership
  -> capability lifecycle records
  -> provider registration/qualification contract
  -> codex adapter implementation
  -> lifecycle integration tests
  -> controlled local acceptance
  -> Chief Architect review
  -> Steward/institutional acceptance
```

## Exit rules

The Codex adapter may execute only with a canonical provider descriptor,
explicit Dispatch authorization, bounded workspace-write paths, declared output
artifacts, and provider receipt validation. A successful process without those
records remains blocked or failed.
