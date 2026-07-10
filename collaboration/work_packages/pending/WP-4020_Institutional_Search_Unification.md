# WP-4020 — Institutional Search Unification

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4012, WP-4014, WP-4015, WP-4019
Classification: Estate Internal

## Objective

Unify the Estate's existing search surfaces into one practical institutional search experience across doctrine, manuals, work packages, validation, residents, mail, history, research, lessons, services, projects, and operational artifacts.

## Required Implementation

- Reuse the Estate knowledge index and existing search commands.
- Provide one query contract with source-type, office, resident, project, classification, date, and status filters.
- Return ranked results with title, path, source type, snippet, provenance, classification, freshness, and owning office.
- Support exact path, phrase, keyword, metadata, and identifier searches.
- Provide privacy-aware result filtering based on caller context.
- Add CLI, API, and Office search-box integration.
- Support result navigation to canonical Office detail surfaces.
- Preserve source-specific truth and distinguish historical, external research, operational, and accepted institutional records.
- Add search diagnostics for stale index, unavailable source, zero results, and permission-filtered results.
- Add deterministic tests for ranking, filters, privacy, provenance, navigation, and backward compatibility.

## Deliverables

- unified institutional search service;
- stable query and result schemas;
- CLI/API/Office integration;
- compatibility wrappers for existing search commands where required;
- `operations/validation/reports/WP-4020_institutional_search.md`;
- `collaboration/work_packages/completions/WP-4020_codex_done.json`.

## Boundaries

Do not create a second index, duplicate source registries, bypass privacy rules, or flatten external research into institutional truth. Do not remove existing search commands without compatibility.

## Acceptance Criteria

- one query can search the major Estate artifact classes;
- results are ranked, source-linked, and privacy-filtered;
- existing search workflows remain functional;
- Office navigation works;
- stale and unavailable states are truthful;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4020_Institutional_Search_Unification.md and do exactly what it says.
```
