# Cleanroom Post-Merge Audit Service

WP-0626 introduces a disposable audit workspace path for automatic post-merge validation. The active development checkout is inspected for hygiene only; it is not stashed, reset, cleaned, switched, or otherwise modified by the audit path.

## Flow

1. A pending/admitted post-merge audit request is claimed.
2. `AuditWorkspaceService` prepares an isolated `git worktree` under the target workspace root.
3. The configured remote is fetched when enabled, `origin/<base_branch>` is resolved when available, and the requested source revision is verified as reachable from the target branch.
4. Deterministic validation runs with the isolated workspace as the validation working tree.
5. Reports, verdicts, Ring 2 prompts, and lifecycle records are written under the configured validation evidence root outside the repository.
6. Successful workspaces are removed automatically; failed workspaces are retained only when target metadata configures `retain_failed_audit_workspaces` truthy.

## Runtime Command

```powershell
python -m estate.cli.main operations-runtime run-once --discover-merges --auto-admit --process-audits --max-audit-requests 5 --json
```

The command processes admitted audit requests up to `max_audit_requests` in one Operations Runtime cycle. A failed audit is recorded and the remaining admitted requests continue until the limit or a fatal service-level failure.

## Evidence

Operational targets may configure:

- `workspace_root`: disposable cleanroom workspaces, for example `A:\EstateRuntime\workspaces\audit\estate-main`.
- `validation_root`: external validation evidence, for example `A:\EstateValidation`.
- `metadata.fetch_enabled`: whether to run `git fetch <remote>`.
- `metadata.remote`: remote name, default `origin`.
- `metadata.retain_failed_audit_workspaces`: retain failed workspaces for diagnosis.

Each verdict includes active/isolated hygiene fields, synchronization status, resolved commit, cleanup status, and the explicit `provider_execution_performed: false` and `dispatch_execution_performed: false` boundaries.
