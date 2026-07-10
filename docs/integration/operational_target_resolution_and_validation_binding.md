# Operational Target Resolution and Validation Binding

Operational target requests resolve external identifiers to canonical target IDs before validation. The canonical Estate target is `estate-main`; external aliases include `estate`, `theestate`, and `ppow1/theestate`.

## CLI

```powershell
python -m estate.cli.main operational-targets resolve --target estate --json
python -m estate.cli.main operational-targets binding --target estate-main --json
python -m estate.cli.main operational-targets aliases --json
python -m estate.cli.main post-merge-audit demonstrate --work-package WP-0620 --pr 199 --json
```

Resolution supports canonical IDs, aliases, repository full names, local paths, and configured environment names. Ambiguous and unknown identifiers return structured failures and are not silently selected.

Validation binding requires an enabled target with `git`, `validation`, and `audit` capabilities plus a source path, base branch, workspace root, and validation root. Provider execution and dispatch execution remain false.
