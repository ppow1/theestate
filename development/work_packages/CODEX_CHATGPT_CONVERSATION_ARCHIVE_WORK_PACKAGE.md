# CODEX WORK PACKAGE — Estate-Wide ChatGPT Conversation Archive and Incremental Synchronization Tool

**Status:** Authorized for full implementation  
**Institutional owner:** The Estate  
**Repository:** `ppow1/theestate`  
**Execution branch:** `work/chatgpt-conversation-archive`  
**Execution environment:** Codex CLI on the Steward's Windows development machine  
**Implementation expectation:** Complete, installed, tested, reusable, production-quality infrastructure  
**Approval model:** One bounded authorization for the entire work package; do not stop for routine implementation approvals

---

## 1. Mission

Design, implement, install, test, document, and deliver a reusable Estate infrastructure tool that creates and maintains a durable local archive of every ChatGPT conversation accessible through the Steward's authenticated browser session.

This tool is not owned by CueMastery and is not limited to CueMastery conversations. It is intended for ongoing Estate-wide use across all current and future repositories, offices, projects, products, investigations, and institutional workflows.

The archive must preserve conversations relating to, including but not limited to:

- `ppow1/theestate`;
- CueMastery;
- ionoge and any other present or future repositories;
- Estate offices and officeholders;
- engineering, governance, operations, research, troubleshooting, planning, and institutional-memory work;
- conversations that do not map cleanly to a single repository.

The exporter archives ChatGPT conversations. It does not assume that repository classification is known at export time. Repository, project, office, and topic classification must remain optional downstream metadata rather than an export filter.

The tool must support:

1. an initial full archive of all accessible conversations;
2. repeatable incremental synchronization;
3. detection of new, changed, renamed, inaccessible, and previously archived conversations;
4. differential reporting after each synchronization run;
5. interruption-safe resume;
6. preservation of prior revisions;
7. machine-readable output suitable for later Codex analysis and Estate knowledge ingestion;
8. manual operation and unattended scheduled operation;
9. reuse independent of any single product repository.

This is not a prototype, scaffold, proof of concept, design exercise, or MVP. The assignment is complete only when the operator has a working installed tool on the Windows machine and the implementation has been exercised successfully against the live authenticated ChatGPT interface.

---

## 2. Institutional Scope and Ownership

The tool is Estate infrastructure.

It must not:

- be named as a CueMastery-specific exporter;
- be installed under a CueMastery-specific directory;
- hard-code CueMastery repository paths, terminology, or assumptions;
- require a conversation to be associated with a GitHub repository before export;
- create one archive per repository as the primary storage model;
- discard conversations because they appear unrelated to software development.

The implementation should use neutral Estate-wide naming, such as:

```text
ChatGPTConversationArchive
chatgpt-conversation-archive
```

Recommended installation root unless implementation evidence requires a better location:

```text
A:\AI\Tools\ChatGPTConversationArchive
```

Recommended default archive root:

```text
A:\AI\Archives\ChatGPT
```

Both paths must be configurable. Machine-specific paths must not be committed as universal defaults without configuration support.

The Estate repository contains the governing work package and integration documentation. The implementation may live in an isolated project directory within the branch or in a clearly separated tool directory in the repository, but it must remain independently maintainable and reusable.

Recommended repository location:

```text
tools/chatgpt-conversation-archive/
```

---

## 3. Governing Execution Instruction

Proceed continuously from repository inspection through implementation, installation, testing, debugging, and operator handoff.

Do not stop after creating a skeleton, source files, or passing unit tests.

Do not ask the Steward for authorization before ordinary engineering actions necessary to finish this bounded assignment, including:

- reading Estate repository guidance;
- creating or modifying files inside the implementation project;
- installing normal project dependencies;
- running formatters, linters, tests, builds, Playwright, and Chrome;
- diagnosing selectors and browser behavior;
- capturing local screenshots, traces, and logs for debugging;
- revising the implementation until acceptance criteria are met;
- creating local configuration templates and operator scripts;
- committing completed work to the designated branch.

When multiple reasonable implementation choices exist, select the safest maintainable approach, document the choice, and continue.

Ask the Steward only when blocked by information or authority that cannot be inferred or safely handled, such as:

- the authenticated Chrome profile cannot be identified automatically;
- ChatGPT presents an interactive challenge requiring the human operator;
- a requested action would expose credentials, delete data, change production infrastructure, incur a new paid service, or leave the work-package boundary;
- the live ChatGPT interface prevents reliable completion despite reasonable selector and fallback strategies.

Do not convert normal engineering uncertainty into approval requests.

---

## 4. Primary Outcome

At completion, the Steward must be able to run one documented command that:

1. launches or attaches to a safe authenticated Chrome profile;
2. inventories all accessible ChatGPT conversations;
3. exports conversations that are new or changed;
4. leaves unchanged conversations untouched;
5. preserves prior revisions;
6. records failures without losing successful work;
7. writes a differential synchronization report;
8. exits with a meaningful status code;
9. can be invoked manually or by Windows Task Scheduler.

The first run must create a complete archive. Later runs must operate incrementally.

---

## 5. Required Technology Baseline

Use the following unless direct implementation evidence requires a better compatible choice:

- **Operating system:** Windows 11
- **Language:** TypeScript
- **Runtime:** supported Node.js LTS
- **Browser automation:** Microsoft Playwright
- **Browser:** installed Google Chrome using an authenticated user-controlled profile
- **Package management:** npm unless repository guidance establishes another standard
- **Testing:** Playwright Test plus a suitable unit-test framework
- **Primary interface:** command line
- **Scheduling compatibility:** Windows Task Scheduler through a non-interactive command

Do not automate credential entry and do not store ChatGPT passwords, session tokens, cookies, or credentials outside the browser profile.

Prefer a dedicated automation Chrome profile initialized through an interactive authenticated session if direct reuse of the normal Chrome profile creates locking or corruption risk. The tool must never silently damage the operator's normal Chrome profile.

---

## 6. Required Operating Modes

### 6.1 Initial Archive

Discover and export every accessible conversation. Support pagination, lazy loading, virtualized lists, and interruption-safe continuation.

### 6.2 Incremental Synchronization

On later runs:

- discover new conversations;
- detect changed content;
- detect renamed conversations;
- detect conversations that are currently inaccessible or absent;
- export only new or changed content;
- preserve previous revisions;
- update indexes and differential reports.

### 6.3 Resume

A failed or interrupted run must resume without duplicating completed work or corrupting the archive.

### 6.4 Validation

Provide a mode that validates archive structure, indexes, hashes, metadata consistency, and revision chains without re-exporting everything.

### 6.5 Diagnostics

Provide a bounded diagnostics mode for selector inspection, browser traces, screenshots, DOM snapshots, and sanitized logs.

### 6.6 Quiet / Scheduled Mode

Provide a non-interactive command suitable for Windows Task Scheduler. It must produce logs and meaningful exit codes without requiring routine operator input.

---

## 7. Conversation Discovery Requirements

The implementation must reliably inventory all accessible conversations, not merely those initially visible in the sidebar.

It must account for:

- virtualized and lazily loaded history;
- scrolling or pagination;
- archived conversations when accessible through the interface;
- projects, folders, or grouping structures when present;
- renamed conversations;
- duplicate visible titles;
- conversations with missing or unusual titles;
- temporary UI failures and retryable load errors.

Use the stable conversation identifier from the ChatGPT URL or another reliable source as the canonical identity. Never use title alone as identity.

Discovery must produce a durable manifest before or during export so interrupted runs can resume deterministically.

---

## 8. Full Conversation Loading

For each conversation, load all available messages and content before finalizing an export.

The exporter must account for:

- long conversations requiring scrolling or staged loading;
- code blocks;
- tables;
- markdown;
- attachments and attachment metadata where accessible;
- images and generated-image references where accessible;
- tool results;
- message edits or alternate branches when the interface exposes them;
- system notices and error messages that materially affect the record;
- timestamps and authorship/role metadata where accessible.

Do not silently omit content because it is outside the initial viewport.

When a content type cannot be exported fully, preserve the strongest available metadata and record the limitation explicitly.

---

## 9. Export Formats

Each conversation must have a canonical machine-readable representation and human-readable renderings.

Required:

1. **Canonical JSON** preserving identity, metadata, message order, roles, content blocks, links, attachments, timestamps when available, export metadata, source URL, and revision information.
2. **Markdown** optimized for human reading and downstream language-model analysis.
3. **HTML** preserving readable structure and code formatting.

Optional PDF may be implemented only after the required formats are complete and reliable.

The JSON schema must be documented and versioned.

---

## 10. Archive Layout

Use a stable neutral layout that is not partitioned primarily by product repository.

Recommended pattern:

```text
<archive-root>/
  archive-manifest.json
  state/
    conversation-index.json
    run-state.json
  conversations/
    <conversation-id>/
      metadata.json
      latest.json
      latest.md
      latest.html
      revisions/
        <revision-id>/
          conversation.json
          conversation.md
          conversation.html
  reports/
    <run-id>/
      summary.json
      summary.md
      new.json
      updated.json
      unchanged.json
      unavailable.json
      failed.json
  logs/
```

Conversation titles may be used in display names, but stable IDs must determine storage identity.

Never automatically delete an archived conversation because it disappears from the current ChatGPT interface. Mark it unavailable while preserving all prior revisions.

---

## 11. State, Hashing, and Change Detection

Maintain an incremental index containing at least:

- conversation ID;
- current title;
- source URL;
- first archived timestamp;
- last discovered timestamp;
- last successful export timestamp;
- last synchronization timestamp;
- current content hash;
- metadata hash if separately useful;
- revision count;
- current status;
- last error;
- last successful revision ID.

Change detection must be deterministic and avoid false updates caused only by volatile UI elements or export timestamps.

Normalize exported content before hashing. Document the normalization strategy.

Never overwrite prior revisions automatically.

---

## 12. Differential Reports

Every synchronization run must produce a summary with counts and identifiers for:

- new conversations;
- updated conversations;
- renamed-only conversations where distinguishable;
- unchanged conversations;
- unavailable conversations;
- failed conversations;
- successfully resumed conversations;
- total discovered;
- total processed;
- run start, end, and duration.

Provide both machine-readable JSON and operator-readable Markdown.

---

## 13. Reliability and Transaction Safety

The implementation must:

- write files atomically where practical;
- use temporary files followed by rename/replace;
- checkpoint progress frequently;
- retain successful exports when later items fail;
- retry transient failures with bounded backoff;
- distinguish retryable and permanent failures;
- avoid duplicate revisions for identical content;
- support clean resume after process termination or machine restart;
- never truncate or replace the entire archive as a routine sync strategy.

A partially failed run must still produce a report and nonzero meaningful exit status.

---

## 14. Browser Session Safety

The tool must not store passwords or copy raw session secrets into project files, logs, reports, or archives.

The browser strategy must be documented and tested for:

- profile locking;
- concurrent Chrome use;
- safe shutdown;
- profile corruption avoidance;
- manual login initialization;
- scheduled execution when the profile is unavailable.

If a dedicated automation profile is used, provide a one-time documented initialization command and a normal sync command.

---

## 15. Configuration

Provide a documented configuration system supporting at least:

- archive root;
- Chrome executable path;
- Chrome profile or automation-profile path;
- headless/headed behavior where supported;
- retry limits;
- timeout values;
- logging level;
- diagnostics path;
- concurrency limits;
- export format toggles;
- optional conversation limits for testing;
- non-interactive mode.

Provide a safe example configuration without credentials or machine secrets.

Environment variables and command-line overrides may be supported, but precedence must be documented.

---

## 16. CLI

Provide a clear CLI with commands equivalent to:

```text
chatgpt-archive init-profile
chatgpt-archive inventory
chatgpt-archive full
chatgpt-archive sync
chatgpt-archive resume
chatgpt-archive validate
chatgpt-archive diagnostics
```

Exact names may differ if documented and coherent.

Required CLI qualities:

- `--help` for every command;
- meaningful exit codes;
- `--quiet` or scheduled mode;
- `--config` support;
- `--archive-root` override;
- dry-run capability for operations that alter archive state where feasible;
- clear progress reporting in interactive mode.

Provide PowerShell launch scripts that work without the operator manually activating a development environment.

---

## 17. Logging and Diagnostics

Logs must include enough context to diagnose failures without exposing credentials or full sensitive conversation text unnecessarily.

Implement:

- structured logs;
- run IDs;
- conversation IDs for per-item errors;
- error categories;
- retry history;
- browser and selector diagnostics;
- optional Playwright traces and screenshots;
- automatic redaction or avoidance of cookies, authorization headers, tokens, and passwords.

Generated logs, traces, screenshots, browser profiles, archives, and machine-specific configuration must be excluded from Git.

---

## 18. Testing

### 18.1 Unit Tests

Test at least:

- filename/path sanitization;
- stable ID handling;
- normalization and hashing;
- revision creation rules;
- manifest updates;
- report generation;
- resume/checkpoint logic;
- retry classification;
- configuration precedence;
- atomic file replacement behavior.

### 18.2 Integration Tests

Use fixtures or controlled pages to test:

- conversation discovery across virtualized lists;
- long-message loading;
- code blocks and tables;
- duplicate titles;
- changed content detection;
- renamed conversations;
- unavailable conversations;
- interrupted export and resume;
- partial failure with retained successes.

### 18.3 Live Acceptance Tests

Against the authenticated ChatGPT interface, demonstrate at least:

1. successful discovery of real conversations;
2. successful export of multiple conversations;
3. successful export of at least one long conversation;
4. successful second sync with unchanged conversations skipped;
5. successful detection of a controlled new or changed conversation when feasible;
6. successful interruption and resume test;
7. successful archive validation;
8. production of differential reports;
9. safe browser-profile behavior.

Do not claim live acceptance if only fixtures were tested.

---

## 19. Selector Resilience

ChatGPT UI selectors may change. Implement layered selector strategies using stable semantics where possible:

- accessible roles and names;
- stable URL patterns;
- durable attributes;
- text patterns only when necessary;
- isolated selector definitions;
- diagnostic output when selectors fail.

Do not scatter brittle selectors throughout the codebase.

Document how to update selectors after UI changes.

---

## 20. Data Quality and Historical Safety

The archive is an institutional record.

The tool must:

- preserve message order;
- distinguish user, assistant, tool, and other roles where visible;
- preserve code fencing and language labels where available;
- preserve links and attachment metadata;
- record export time and exporter version;
- record incomplete or failed extraction explicitly;
- never present a partial extraction as complete;
- preserve prior successful exports when a newer extraction fails;
- never automatically purge historical revisions.

---

## 21. Estate Integration Boundary

This work package creates the durable source archive and synchronization capability.

It must produce output suitable for future Estate ingestion, indexing, classification, summarization, and cross-repository analysis.

The exporter itself must not require repository assignment before archiving. Optional metadata fields may later record:

- related repositories;
- Estate office;
- project or product;
- topic tags;
- sensitivity classification;
- ingestion status.

These fields must remain optional and must not block export.

Building the full downstream Estate knowledge graph, semantic search service, or repository reconciliation engine is outside this work package unless needed minimally to validate output compatibility.

---

## 22. Scheduling

Support Windows Task Scheduler through a stable non-interactive command.

Provide:

- an operator-ready PowerShell script for normal sync;
- documented Task Scheduler setup instructions;
- safe behavior when Chrome or the automation profile is locked;
- logs and reports for unattended runs;
- nonzero exit codes on actionable failure.

The exporter does not need to register the scheduled task automatically unless implementation evidence shows that doing so is safe and useful.

---

## 23. Performance

The implementation should avoid reopening or re-rendering unchanged conversations unnecessarily when reliable metadata permits skipping work.

Use bounded concurrency that does not destabilize Chrome or trigger rate/security defenses.

Large archives must remain manageable through incremental state rather than full reprocessing on every run.

Document expected performance and known limitations based on live testing.

---

## 24. Documentation

Required documentation:

- architecture overview;
- installation instructions;
- one-time browser-profile initialization;
- normal full archive command;
- normal incremental sync command;
- scheduled operation;
- configuration reference;
- archive schema;
- recovery and resume procedures;
- selector maintenance guide;
- privacy and security notes;
- troubleshooting guide;
- uninstall or relocation procedure;
- known limitations;
- acceptance report.

Documentation must use Estate-wide language and must not describe the tool as CueMastery-owned or CueMastery-specific.

---

## 25. Installation and Operator Handoff

Leave the tool installed and runnable from a neutral machine path.

Provide operator scripts equivalent to:

```text
Initialize-ChatGPTConversationArchive.ps1
Run-ChatGPTConversationArchiveFull.ps1
Run-ChatGPTConversationArchiveSync.ps1
Validate-ChatGPTConversationArchive.ps1
```

Exact names may differ if clear and consistent.

Scripts must begin with `CLS`, provide actionable errors, and avoid requiring the operator to edit source code.

---

## 26. Acceptance Criteria

The work package is complete only when all feasible criteria below are met and documented:

- Estate-wide neutral naming is used throughout;
- no CueMastery-specific ownership or path remains;
- source, tests, scripts, configuration examples, and documentation exist;
- dependencies install successfully;
- build succeeds;
- automated tests pass;
- live authenticated discovery succeeds;
- initial archive succeeds on a representative set and is capable of full traversal;
- second sync skips unchanged conversations;
- changed/new detection is demonstrated where feasible;
- prior revisions are preserved;
- interruption and resume are demonstrated;
- differential reports are generated;
- archive validation succeeds;
- browser profile safety is demonstrated;
- scheduled-mode command is documented and tested as far as practical;
- the operator has one exact command for routine sync;
- `docs/ACCEPTANCE_REPORT.md` maps each requirement to evidence or a clearly stated external blocker.

---

## 27. Prohibited Completion Claims

Do not claim completion based only on:

- repository scaffolding;
- generated code that has not run;
- unit tests alone;
- mocked browser pages alone;
- a successful build;
- export of a single short conversation;
- manual instructions without an installed tool;
- a plan for later live testing;
- a CueMastery-specific implementation.

---

## 28. Scope Exclusions

Unless directly required for reliable export, this work package does not authorize:

- deleting ChatGPT conversations;
- editing ChatGPT conversations;
- automating credential entry;
- bypassing security controls or interactive challenges;
- uploading the archive to third-party services;
- exposing conversation content publicly;
- creating a complete Estate semantic-search platform;
- modifying unrelated Estate product code;
- reorganizing unrelated repositories.

---

## 29. Required Final Codex Response

When complete, return a concise operator handoff containing:

1. exact installation path;
2. exact archive path;
3. exact routine synchronization command;
4. exact full-archive command;
5. exact validation command;
6. browser-profile strategy and initialization status;
7. tests executed and results;
8. live acceptance tests executed and results;
9. reports and acceptance-report locations;
10. files and commits created;
11. remaining limitations or genuine external blockers;
12. confirmation that the implementation is Estate-wide and not CueMastery-specific.

Do not substitute a development narrative for the operator handoff.

---

## 30. Codex Start Instruction

Read this work package in full, then inspect `AI_START_HERE.md`, `AI_HINTS.md`, and applicable Estate repository guidance before implementation.

This work package is fully authorized. Execute continuously through implementation, installation, automated testing, live acceptance testing, documentation, commit, and operator handoff. Do not stop for routine implementation approval. Interrupt the Steward only for a genuine external blocker within the terms above.
