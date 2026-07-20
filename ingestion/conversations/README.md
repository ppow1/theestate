# Conversation Ingestion

This directory is the dedicated intake root for archived AI conversation files that will be processed by the Estate conversation-ingestion engine.

It is intentionally separate from worker reflection, renewal, onboarding, and continuity-package records.

## Production input contract

- Repository-safe private intake: `ingestion/conversations/private/` (gitignored).
  The production command creates it automatically when it is missing. Git does not
  preserve empty ignored directories, so its absence after a clone or pull is normal.
  Copy private archives there after pulling; no manual directory setup is required.
- Accepted source extensions: `.mhtml`, `.mht`, `.html`, `.htm`, `.txt`, `.text`, and
  `.md`; existing normalized bundles are directories containing `manifest.json` and
  `messages.jsonl`.
- Directories accept multiple files. Discovery is non-recursive unless `--recursive`
  is explicitly supplied. `--archive-filter TEXT` limits sources by filename.
- Every source is SHA-256 registered before analysis. Identical content is processed
  once and duplicate paths remain visible in `archive_inventory.json`.

Plain text must label each turn (`Steward:`, `User:`, `Assistant:`, or `ChatGPT:`).
HTML must retain `data-message-author-role` elements. MHTML uses the largest HTML MIME
part. Files that cannot satisfy these contracts fail without partial promotion.
Filenames are descriptive only: identity and rerun location derive from content hashes.
Conversation archives can contain private material; do not commit them unless repository
policy and the data owner explicitly authorize that disclosure.

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

## Pending-definition matched runtime-canon recovery (WP-4212)

The recovery command accepts one archive, several archives, a directory of
archives, or existing WP-4208 bundle directories. It scans assistant messages
without using conversational assignment as a filter, resolves substantive output
against `collaboration/work_packages/pending/`, assesses completeness and
truncation, reconciles cross-archive duplicates, and stages qualifying evidence:

```bash
PYTHONPATH=src python -m estate.core.runtime_canon_recovery \
  ingestion/conversations/archive-one.mhtml \
  ingestion/conversations/archive-two.mhtml \
  --output-root staging/runtime_canon_recovery
```

Production run on Windows (from `A:\theestate`):

```powershell
.\scripts\Invoke-RuntimeCanonRecovery.ps1
```

This command creates the intentionally gitignored `private/` intake if necessary,
scans it recursively, runs runtime-canon recovery, and writes the established staging
output under `staging/runtime_canon_recovery/`. It prints both the recovery-report
and review-queue locations. An empty intake is a successful, non-fatal run with clear
instructions showing the resolved intake path.

To process an explicitly named archive anywhere under `ingestion/conversations/`
(including an archive outside `private/`), pass its path directly. Quoting preserves
paths containing spaces:

```powershell
.\scripts\Invoke-RuntimeCanonRecovery.ps1 "ingestion\conversations\Archive With Spaces.mhtml"
```

Only the default `private/` directory is scanned implicitly. The command does not
scan the whole `ingestion/conversations/` tree; that broader directory is scanned
only if the operator explicitly supplies it.

Use `--dry-run` to assess without staging a supporting document, or
`--identifier-filter WP-4212` to process one identifier. `--output-root` selects the
derived evidence location. Useful additional options are `--pending-root`,
`--archive-filter`, `--machine-readable`, and `--strict`.
Strict mode exits 2 for review blocks; fatal input, index, parsing, or generation
errors exit 3. Default mode still exits 3 for fatal diagnostics, while ordinary
review blocks remain inspectable without making batch processing fail.

Each content-addressed run emits `pending_work_package_index.json`,
`pending_index_repair_report.json`, `archive_inventory.json`,
`runtime_canon_candidates.json`, `definition_match_report.json`,
`candidate_assessment_report.json`, `candidate_reconciliation_report.json`,
`supporting_document_manifest.json`, `runtime_canon_review_queue.json`,
`runtime_canon_recovery_report.md`, `pending_index_repair_report.md`,
`production_activation_report.md`, and `promotion_block_report.md`. Inspect the
recovery report for counts and the review queue for per-WP human actions. Proposed documents live only below the run's
`supporting_documents/` staging directory. They include a provenance preamble and
the mechanically newline-normalized assistant body. The engine never writes to a
proposed destination, never modifies a pending definition, and never promotes a
derived document automatically.

An unchanged source and pending index resolve to the same run identifier, so rerunning
is resumable and atomically replaces deterministic artifacts. Missing named archives
are not errors unless an operator requires them; place them in the private intake and
rerun. Index diagnostics block only an affected ambiguous/invalid identifier. To request
promotion, submit the staged document and manifest through normal human review—never
copy it over a pending definition or bypass the promotion block report.

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

## MHTML character encoding

HTML MIME parts are decoded using their declared charset when it is valid. Charset
names are normalized through the standard codec registry, so common aliases such as
`cp1252` and `Windows-1252` are handled consistently. If the declaration is missing
or invalid, or strict decoding fails, ingestion tries UTF-8 and then Windows-1252.
As a final non-fatal recovery, Windows-1252 is decoded with replacement so undefined
Windows bytes remain visible as replacement characters rather than aborting the run.

The ingestion manifest records the declared charset, codec actually used, whether a
fallback occurred, replacement-character count, MIME filename, and decoding
diagnostics. Runtime-canon recovery copies that evidence into its archive inventory,
counts archives with decoding warnings, and prints the warnings in its report while
continuing whenever extraction remains safe. MIME encoded words in locations,
filenames, and metadata are decoded; malformed values are preserved safely.

Fallback warnings mean the derived transcript requires human review; they do not
change its non-canonical status and do not authorize promotion. Source archives are
always read as immutable bytes, SHA-256 registered from those exact bytes, and never
rewritten or silently transcoded. Only separate derived UTF-8 artifacts are written.
