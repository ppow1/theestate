# WP-0527 Unified Search Contract

This installed contract defines `estate.office_unified_search.v1` and is **installed WP-0531 work**. WP-0531 may install or adapt it into active Office modules.

## Query Contract

A query is a JSON-compatible object with:

- `schema`: `estate.office_unified_search.v1`.
- `installed_by_wp_0531`: `true` after WP-0531 installation.
- `query`: free-text user query.
- `categories`: any supported result categories: `work_package`, `resident`, `project`, `validation`, `decision`, `git_evidence`, `artifact`, `conversation`, and `command`.
- `filters`: typed filters such as `tag`.
- `include_stale`: whether stale results may remain visible.
- `limit`: maximum result count.

## Result Contract

Each result includes:

- `id`, `category`, `title`, and `excerpt`.
- `relevance`, a deterministic score that favors title, id, tag, then body matches.
- `filters.tags`, allowing Office UI chips and follow-up filtering.
- `freshness`, with `fresh`, `stale`, `missing`, or `unknown` state and source existence details.
- `source.path` / `source.artifact`, preserving source-artifact traceability.
- `navigation.destination`, expected to be a real Office destination such as `office://work-packages/WP-0527`.

## Safe Command Contract

Command palette invocation only accepts registered `SafeAction` entries. Arbitrary shell, Python, URL, file, handler strings, and obvious shell metacharacter command IDs are rejected before registry lookup.

## Settings-Aware Query Memory

Recent searches and pinned queries are exposed as pure state transforms and only write when callers pass explicit settings permission flags.
