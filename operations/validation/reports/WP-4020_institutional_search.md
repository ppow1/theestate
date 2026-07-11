# WP-4020 Institutional Search Validation Report

## Summary

Implemented unified institutional search as a local retrieval projection over the existing Estate knowledge index. The service provides a stable query/result contract for CLI, API-style Python callers, and the Office search surface without creating a second index or changing canonical source-of-truth rules.

## Implemented Scope

- Reuses `estate_knowledge_index.query_index`, `inspect_index`, and `status` for all retrieval and diagnostics.
- Adds unified filters for source type, office, resident, project, classification, date, and status.
- Returns ranked results with title, path, source type, snippet, provenance, classification, freshness, owning office, score, and canonical Office navigation metadata.
- Supports exact path, phrase, keyword, metadata, and identifier style searches through the shared index haystack and metadata filters.
- Preserves privacy-aware filtering; protected private records require explicit include-private intent and an authorized caller context.
- Adds diagnostics for stale index state, unavailable source locations, zero results, and permission-filtered matches.
- Preserves existing `estate-search`, `knowledge-index query`, and `global-search` compatibility while adding `institutional-search` as the unified CLI entry point.
- Integrates the Office search box by adding unified institutional result records and diagnostics to the existing global search panel payload.
- Distinguishes accepted institutional records, operational records/evidence, historical records, external research, and retrieval projections in result provenance.

## Validation Commands

- `python -m pytest tests/test_unified_institutional_search.py tests/test_institutional_search.py tests/test_estate_knowledge_index.py tests/test_global_search_command_palette.py -q`

## Result

Focused institutional search, compatibility, knowledge index, and Office command-palette tests passed.
