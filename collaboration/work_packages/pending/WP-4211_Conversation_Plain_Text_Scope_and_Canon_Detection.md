# WP-4211 — Conversation Plain-Text Scope and Canon Detection

Status: Pending
Owner: Institutional Ingestion Implementation Stream
Execution Target: Codex
Depends On: WP-4208, WP-4209, WP-4210, `src/estate/core/conversation_archive_ingestion.py`, `src/estate/core/conversation_specification_extraction.py`
Classification: Estate Internal

## Objective

Extend the conversation-ingestion pipeline so it can ingest plain-text copy/paste conversation exports, reconstruct the active Steward assignment over time, detect actual runtime-canon production across real heading variants, and report scope violations, ignored corrections, false completion claims, and failures to execute after `go`.

The implementation must treat Steward scope instructions as an ordered timeline rather than one static range. Later explicit corrections supersede earlier scope declarations. Assistant acknowledgements do not redefine scope unless they accurately reflect the Steward's instruction.

The system must produce deterministic, review-only artifacts and must not promote chat output into canon automatically.

## Required Implementation

### 1. Plain-Text Conversation Intake

Accept UTF-8 plain-text conversation captures in addition to MHTML.

The intake layer must:

- preserve