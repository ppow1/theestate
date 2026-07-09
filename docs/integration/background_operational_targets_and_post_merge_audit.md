# Background Operational Targets and Post-Merge Audit

WP-0618 adds a registered operational target model, file-backed target control surface, Git hygiene status, and deterministic post-merge audit request/verdict artifacts.

## CLI

```bash
python -m estate.cli.main operational-targets list --json
python -m estate.cli.main operational-targets show --target estate-main --json
python -m estate.cli.main operational-targets enable --target estate-main --json
python -m estate.cli.main operational-targets pause --target estate-main --json
python -m estate.cli.main operational-targets disable --target estate-main --json
python -m estate.cli.main operational-targets import-candidate --target cue-mastery --json
python -m estate.cli.main operational-targets status --json
```

## Runtime boundaries

The function observes targets and creates governed requests. It does not approve, merge, repair, stash, dispatch, or execute providers. Runtime validation evidence defaults outside the active source repository under `A:/EstateRuntime/validation`, while source-controlled receipts, recipes, contracts, and curated reports remain in the repository.

## Artifacts

- `runtime/operational_targets/registry.json`
- `runtime/operational_targets/status/latest.json`
- `runtime/post_merge_audit/requests/<audit_id>.json`
- `runtime/post_merge_audit/verdicts/<audit_id>.json`
- `runtime/post_merge_audit/ring2_prompts/<audit_id>.md`
