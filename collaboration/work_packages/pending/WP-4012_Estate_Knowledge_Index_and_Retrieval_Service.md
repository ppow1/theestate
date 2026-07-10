# WP-4012 — Estate Knowledge Index and Retrieval Service

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Implement a governed local knowledge index that discovers, catalogs, and retrieves Estate artifacts for residents, offices, and the Steward without creating a second source of institutional truth.

## Required Implementation

- Reuse existing document registry, global search, institutional search, discovery, and provenance mechanisms where available.
- Index manuals, doctrine, work packages, validation reports, architectural decisions, onboarding material, lessons learned, resident artifacts, and constitutional records.
- Persist normalized metadata including path, title, artifact type, owner, classification, modified time, source hash, and provenance.
- Provide incremental reindexing based on changed files.
- Provide keyword and metadata filtering first; optional semantic indexing may be added only as a local adapter behind the same contract.
- Add CLI commands for rebuild, incremental update, status, inspect, and query.
- Add a reusable query API for Alfred, Helen, Grace, Historian, Research, and Office surfaces.
- Return ranked results with source paths and snippets.
- Detect stale or missing index entries.
- Never treat indexed text as newly approved institutional truth.

## Deliverables

- core local index and retrieval service;
- versioned schemas;
- CLI integration;
- existing Office/search surface integration;
- tests for indexing, incremental refresh, filtering, ranking, provenance, and stale detection;
- `operations/validation/reports/WP-4012_estate_knowledge_index.md`;
- `collaboration/work_packages/completions/WP-4012_codex_done.json`.

## Boundaries

Do not introduce a mandatory external vector database, cloud embedding service, new constitutional office, or duplicate document registry. Do not index protected private content into unrestricted search results.

## Acceptance Criteria

- local artifacts are discoverable through one reusable query contract;
- results include provenance and classification;
- incremental refresh works;
- private content remains filtered;
- existing search surfaces remain compatible;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4012_Estate_Knowledge_Index_and_Retrieval_Service.md and do exactly what it says.
```
