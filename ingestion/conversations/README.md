# Conversation Ingestion

This directory is the dedicated intake root for archived AI conversation files that will be processed by the Estate conversation-ingestion engine.

It is intentionally separate from worker reflection, renewal, onboarding, and continuity-package records.

## Current intake format

- ChatGPT conversation archives saved as `.mhtml`

## Initial test archive

Upload the Chief Architect archive directly into this directory using a descriptive filename such as:

`Chief_Architect_Renewal_Verification_2026-07-19.mhtml`

## Handling rules

- Treat uploaded archives as immutable source evidence.
- Do not edit or overwrite an uploaded archive.
- Generated extraction records, classifications, and proposed repository artifacts must be written to separate run-specific output paths created by the ingestion engine.
- No extracted proposal becomes Estate canon without the normal review and approval process.

This README establishes the directory so source archives can be uploaded through the GitHub web interface before the ingestion engine is implemented.

## Ingestion

Run the engine from the repository root (the source file is opened read-only):

```bash
PYTHONPATH=src python -m estate.core.conversation_archive_ingestion \
  ingestion/conversations/Chief_Architect_Renewal_Verification_2026-07-19.mhtml
```

Output is content-addressed at `derived/<source stem>/<first 16 SHA-256 characters>/`.
Re-running an unchanged source atomically replaces the same deterministic artifacts.
Each bundle contains a source-hash manifest, JSONL message records, a readable
verbatim extraction, and a separate derived-review record. The latter starts empty:
review and the normal approval process are required before any institutional adoption.

Use `validate_bundle` from `estate.core.conversation_archive_ingestion` to verify a
bundle against its immutable source. A changed source gets a new run identifier;
message or source tampering causes validation to fail.

## Extracting work-package specification candidates

After ingestion, the successor engine classifies conversation messages, extracts
structured assistant runtime-canons, checks a deliberately bounded WP set, and
writes review-only candidates:

```bash
PYTHONPATH=src python -m estate.core.conversation_specification_extraction \
  ingestion/conversations/design-chat.mhtml \
  --expected "WP-4107 through WP-4116"
```

`--expected` also accepts `WP-4117..WP-4126`, `WP-4127:WP-4130`, or a comma-separated
identifier list. Output is content-addressed under
`staging/conversation_specifications/<run-id>/`. `validation_report.json` always
enumerates found, missing, duplicate, ambiguous, and unexpected identifiers. A
blocked report causes CLI exit status 2; the report remains available for review.

Candidates preserve headings, paragraphs, lists, tables, fenced code, and
indentation from the archive's message HTML. Each candidate carries archive hash,
conversation location, message ID and sequence, extraction run, and WP provenance.
Suggested destinations are metadata only: the command never writes there, never
edits source archives, and rejects any suggestion targeting a pending definition.
Human review and the normal adoption process remain mandatory.

## Plain-text scope and runtime-canon validation (WP-4211)

Label every turn in a UTF-8 copy/paste capture with `Steward:`, `User:`,
`Assistant:`, or `ChatGPT:`. Run the scope-aware successor pipeline with:

```bash
PYTHONPATH=src python -m estate.core.conversation_scope_validation \
  ingestion/conversations/design-chat.txt
```

The command also accepts MHTML and reuses the same WP-4208 ingestion bundle. It
derives the authoritative scope only from ordered Steward/user turns; later explicit
corrections supersede earlier assignments, while assistant restatements remain
non-authoritative. Production-style Markdown, bold, `Work Package`, and `Runtime
Canon` WP headings are recognized.

The content-addressed review directory contains `scope_timeline.json`,
`execution_timeline.json`, `scope_validation_report.json`,
`conversation_diagnostics.json`, and `promotion_block_report.md`. Exit status 2
means a review-blocking diagnostic was found. Every result remains non-canonical,
review-required material and automatic promotion is always prohibited.
