# SERIES TASK WP-0027 — Institutional Search v1

## Codex Command
Read `collaboration/work_packages/pending/WP-0027_SERIES_institutional_search_v1.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0026 Generated Artifact Policy so search can distinguish source records from generated projections.

## Mission
Implement a local institutional search index for key Estate artifacts so workers do not depend on GitHub search to find required documents, messages, work packages, and operational records.

## Why This Is Next
Onboarding and mailbox review exposed a practical problem: GitHub search and connector access are not reliable enough for workers to locate institutional documents by concept. The Estate needs a local-first searchable index built from known repository paths.

## Scope
Create a bounded search/index module such as:

- `src/estate/core/institutional_search.py`

Index text artifacts from selected locations, including where present:

- `AI_HINTS.md`
- `AI_START_HERE.md`
- `constitution/`
- `docs/`
- `collaboration/messages/`
- `collaboration/work_packages/`
- `operations/`
- `runtime/` reports only where policy allows
- `archive/institutional_memory/`

## Expected Outputs
- Search index artifact such as `runtime/search/institutional_search_index.json`.
- Search report/CLI output for keyword queries.
- CLI if consistent with existing patterns, for example:

```bash
PYTHONPATH=src python -m estate.cli.main estate-search "Chief Architect memorandum" --json
```

## Behavior Requirements
- Index files by path, title/heading if detected, artifact type, and short excerpt.
- Respect Generated Artifact Policy classifications where available.
- Do not treat generated projections as authoritative unless policy permits.
- Missing folders should be warnings, not fatal errors.
- Keep search simple: keyword/substring matching is acceptable for v1.

## Tests
Add tests for:

- indexing representative documents
- excluding or labeling generated artifacts according to policy
- keyword search returning path and excerpt
- missing directory warnings
- JSON output

## Constraints
Do not add external search services. Do not require cloud services. Do not create embeddings or vector databases in v1. Do not redesign onboarding or governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0027_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded local tooling after CA verification. Escalate to Class B only if implementation introduces external dependencies or changes source-of-truth policy.
