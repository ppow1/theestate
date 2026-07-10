# WP-4015 — Research Office Source Intelligence and Monitoring

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4012
Classification: Estate Internal

## Objective

Implement the Research Office as a local evidence-management and source-intelligence service for external research, technology monitoring, product intelligence, literature review, and cited recommendations.

## Required Implementation

- Create versioned research-request, source, claim, finding, recommendation, and monitoring-record schemas.
- Support source-quality ratings, publication date, retrieval date, provenance, confidence, conflicting evidence, and citation links.
- Provide local intake for web research results, uploaded documents, technical papers, product findings, and manually supplied evidence.
- Add CLI commands for request creation, source intake, finding review, report generation, and monitoring status.
- Integrate with the Estate knowledge index while keeping external research distinct from accepted institutional truth.
- Support recurring monitoring records without implementing a new scheduler; reuse existing background operations where available.
- Provide concise Office summaries and source inspection.
- Add tests for citation integrity, duplicate sources, conflicting claims, stale findings, and unsupported recommendations.

## Deliverables

- Research Office runtime and local store;
- schemas and examples;
- CLI and existing Office integration;
- sample local research workflow;
- `operations/validation/reports/WP-4015_research_office_runtime.md`;
- `collaboration/work_packages/completions/WP-4015_codex_done.json`.

## Boundaries

Do not treat external claims as institutional truth. Do not add cloud-only dependencies, a new scheduler, or a duplicate knowledge index. Do not fabricate citations or source access.

## Acceptance Criteria

- findings are traceable to sources;
- conflicting evidence is preserved;
- stale research is detectable;
- monitoring reuses existing runtime mechanisms;
- reports distinguish evidence, inference, and recommendation;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4015_Research_Office_Source_Intelligence_and_Monitoring.md and do exactly what it says.
```
