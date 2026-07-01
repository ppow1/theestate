# Parking Lot Seed: Retrieval Reliability and Spiderbot Knowledge Index

Status: Intake
Classification: Estate Internal
Originator: Pat / Steward
Captured By: Chief Architect #2
Date Captured: 2026-06-30
Priority: High
Target Board: Future Operations Board / Parking Lot
Current Status: Deferred institutional thinking

## Purpose

Capture two Steward-originated institutional observations for future Operations Board ingestion.

These items should be moved into the formal Parking Lot once WP-OPS-001 implements the Estate Operations Board.

## Item 1: Retrieval Reliability Principle

### Summary

The Estate must preserve hard-won operational knowledge about tool behavior, especially retrieval limitations.

Pat has observed through repeated experience that GitHub connector search can fail even when a file exists. Therefore, workers must not conclude that a file is absent merely because one search method fails.

### Proposed Principle

Tool limitations are not evidence of repository state.

An implementation's inability to retrieve an artifact does not constitute proof that the artifact does not exist. Before concluding that institutional information is absent, use an appropriate retrieval method, direct path fetch, local inspection, or report retrieval uncertainty.

### Practical Rule

When searching for repository information:

1. Search may be used for discovery, but it is not authoritative.
2. If a path is known, fetch by direct path.
3. If connector search fails, try direct GitHub API-style calls or local repository inspection.
4. If multiple methods fail, report retrieval uncertainty rather than asserting absence.
5. Do not argue against the Steward's direct evidence of a file or artifact.

### Suggested Home

- Estate Engineering Matrix
- Estate Manual
- Worker Seed Chat Template
- Worker Readiness Record
- Future Retrieval/Discovery standards

## Item 2: Spiderbot / Knowledge Index Worker

### Summary

The Estate needs a future worker or service that crawls institutional information and publishes searchable tags, references, and knowledge index entries.

The goal is to make prior chats, documents, artifacts, and institutional decisions discoverable without relying on fragile manual memory or one-off searches.

### Working Name

Spiderbot is a loose working term only.

Possible future names:

- Estate Knowledge Indexer
- Marie Index Worker
- Eleanor-Marie Knowledge Crawler
- Institutional Search Worker
- Archive Discovery Worker

### Possible Office Alignment

Likely shared between:

- Marie: researches, connects, enriches, curates meaning.
- Eleanor: preserves official institutional records and archive integrity.

Marie may own enrichment and semantic tagging.
Eleanor may own official record boundaries and archive integrity.

### Candidate Responsibilities

- Crawl approved Estate documents.
- Crawl approved history records.
- Crawl promoted chat artifacts.
- Extract topics, tags, references, relationships, and source locations.
- Build a local-first knowledge base.
- Support search over prior decisions and conversations.
- Preserve source references.
- Avoid promoting private or Local Only material without boundary approval.
- Support future workers with better retrieval context.

### Boundary Requirements

The worker must respect classification and promotion rules.

It must not publish or index Local Only content into shared repositories without explicit approval.

### Suggested Home

- Parking Lot
- Future Discovery roadmap
- Marie roadmap
- Eleanor archive roadmap
- Local-first infrastructure roadmap

## Parking Lot Notes

These are not active implementation tasks yet.

They should be reviewed during Operations Board setup and converted into formal Parking Lot entries once the board exists.
