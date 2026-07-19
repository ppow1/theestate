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
