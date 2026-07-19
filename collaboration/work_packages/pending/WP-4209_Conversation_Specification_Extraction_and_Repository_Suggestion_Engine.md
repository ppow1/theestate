# WP-4209 — Conversation Specification Extraction and Repository Suggestion Engine

Status: Pending
Owner: Institutional Ingestion Implementation Stream
Execution Target: Codex
Depends On: WP-4208, src/estate/core/conversation_archive_ingestion.py, ingestion/conversations/README.md
Classification: Estate Internal

## Objective

Extend the deterministic conversation archive ingestion foundation created by WP-4208 so that completed Estate work-package design chats can be converted into reviewable, provenance-preserving, one-artifact-per-work-package specification candidates and repository destination suggestions without silently promoting chat content into accepted canon.

The implementation must support the operational workflow in which multiple ChatGPT conversations are run in parallel by Estate Chat Walker, each conversation is bounded to a specific work-package range, and completed conversations are saved as immutable MHTML archives. The engine must identify the completed runtime-canon/specification sections in those archives, preserve their structure, associate them with the correct pending work packages, validate expected coverage, and prepare deterministic repository-write candidates for human review.

The first