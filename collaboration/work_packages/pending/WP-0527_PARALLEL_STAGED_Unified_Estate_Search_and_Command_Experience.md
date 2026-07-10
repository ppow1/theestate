# WP-0527 - Unified Estate Search and Command Experience

## Codex Command
Read collaboration/work_packages/pending/WP-0527_PARALLEL_STAGED_Unified_Estate_Search_and_Command_Experience.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Build a staged unified search and safe command experience across work packages, residents, projects, validation, decisions, Git evidence, artifacts, and conversations.

## Required Capabilities
- one query contract across existing Estate indexes and artifacts;
- typed result categories, relevance, filters, and source freshness;
- direct navigation to real Office destinations and source artifacts;
- command palette invocation of registered safe Office actions only;
- recent searches and pinned queries where existing settings permit;
- no arbitrary shell, Python, URL, or handler execution.

## Staging Requirements
Create under `collaboration/workstreams/WP-0527/`:

```text
install_manifest.json
staged/office_unified_search.py
staged/test_office_unified_search.py
unified_search_contract.md
validation_notes.md
rollback_notes.md
```

Do not modify shared active Office files. WP-0531 performs installation.

## Conflict Surface
Expected final targets include a dedicated search module, command-palette adapter, Office registration hooks, tests, and docs. Declare overlaps with `global_search_command_palette.py` and WP-0520.

## Validation
Prove cross-domain search, filtering, direct navigation, stale/missing source handling, safe registered action invocation, and rejection of arbitrary commands.

## Completion Receipt
Create `collaboration/work_packages/completions/WP-0527_codex_done.json` and state that staged work is not installed work.
