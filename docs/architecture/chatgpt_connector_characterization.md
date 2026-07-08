# ChatGPT Connector Characterization

Status: Architectural Characterization  
Work Package: WP-CHATGPT-CLI-001  
Author: Chief Architect #6  
Classification: Estate Internal

## Purpose

This document characterizes ChatGPT connector and tool capabilities relevant to the Estate.

This is not an implementation guide. It defines how the Estate should reason about ChatGPT as a connector-backed planning and repository service.

## Source Note

ChatGPT capabilities are not static. OpenAI release notes and help documentation change over time. The Estate should treat ChatGPT connector capability as discoverable operational state rather than permanent doctrine.

## General Capability Categories

ChatGPT may have access to some or all of the following, depending on workspace, plan, account settings, connected apps, and session environment:

- GitHub connector
- Gmail
- Google Calendar
- Google Contacts
- file uploads
- web search
- Deep Research
- image input and generation
- voice
- memory
- personal context
- scheduled tasks
- data analysis / Python environment
- document generation/editing tools
- repository write tools

The Estate must not assume every ChatGPT session has every tool.

## GitHub Connector

### Observed / Expected Capabilities

A GitHub connector can support repository operations such as:

- fetch repository metadata,
- search files,
- fetch file contents,
- create files,
- update files,
- delete files,
- inspect pull requests,
- fetch PR metadata,
- fetch PR diffs and patches,
- inspect changed filenames,
- read issue and PR comments,
- inspect GitHub Actions metadata where available.

### Strengths

- Good for governance and documentation updates.
- Good for repository orientation when the repository and paths are known.
- Good for PR and issue triage.
- Useful when local CLI is unavailable.

### Weaknesses

- Connector output may be truncated.
- Repository discovery may be incomplete or slower than direct local access.
- Write actions may require explicit user approval.
- Connector actions do not prove local runtime success.
- GitHub repository state may lag behind local source of truth.
- GitHub is not the Communication Bus.

### Estate Policy

Use GitHub connector for:

- governance documentation,
- architecture documents,
- work package publication,
- repository review,
- PR/issue review,
- shared-state promotion.

Do not use GitHub connector as:

- the primary local execution engine,
- the authoritative local runtime observer,
- the mailbox system itself,
- a substitute for audit or validation.

## Gmail / Calendar / Contacts

### Potential Uses

- scheduling and coordination,
- reading or drafting external communication,
- identifying contacts,
- creating calendar events,
- reviewing email context when explicitly authorized.

### Boundary Considerations

These tools commonly contain sensitive personal or external information.

Use requires heightened boundary awareness and may require Ingrid / Privacy and Boundary review depending on classification, content, and intended output.

## Web Search

### Potential Uses

- current facts,
- public documentation,
- product or provider capability changes,
- external technical references,
- official source verification.

### Weaknesses

- Web results may be stale, noisy, or non-authoritative.
- Public sources are not Estate authority.
- Web findings must be cited and distinguished from Estate doctrine.

## Deep Research

### Potential Uses

- multi-source external research,
- strategic reports,
- capability landscape analysis,
- complex technology comparisons.

### Weaknesses

- Higher latency.
- May consume limited research capacity.
- Output still requires review.
- Not a replacement for Estate authority or local validation.

## Image Input / Image Generation

### Potential Uses

- Office of the Steward screenshot review,
- UI/UX operational assessment,
- architectural visual critique,
- visual onboarding artifact planning,
- generated concept art when approved.

### Boundary Considerations

Generated or uploaded images may contain private content, resident identity material, or sensitive operational information.

Generated media should default to Local Only unless intentionally promoted.

## Voice

### Potential Uses

- Steward brainstorming,
- rapid planning discussion,
- accessibility,
- live working sessions.

### Weaknesses

- Voice sessions may expose less tool access than text sessions.
- Transcription errors can affect precision.
- Long architectural tasks should persist conclusions into repository artifacts.

## Memory and Personal Context

### Potential Uses

- preserving user preferences,
- maintaining style and workflow continuity,
- reducing repeated explanation.

### Boundary Considerations

Memory is useful but not authoritative Estate record.

Estate authority remains:

1. Steward decision,
2. Constitution / governance,
3. Manual / architecture,
4. repository records,
5. audit / validation evidence,
6. conversation memory only after those.

## Data Analysis / Python

### Potential Uses

- local file analysis in the chat environment,
- spreadsheet and CSV analysis,
- charts,
- structured transformations,
- bundle inspection.

### Weaknesses

- Chat sandbox is not `A:\theestate`.
- Results are not local Estate execution unless intentionally transferred.
- Should not be confused with LEAP or local authority execution.

## Scheduled Tasks

### Potential Uses

- reminders,
- recurring external checks,
- scheduled summaries.

### Weaknesses

- Not a replacement for Alfred scheduling or the future Orchestrator.
- May not have local Estate access.

## Connector Risk Categories

### Low Risk

- Reading public web sources.
- Drafting governance text from supplied files.
- Reviewing uploaded screenshots.
- Creating proposed documents for review.

### Moderate Risk

- Writing to GitHub.
- Reading repository-private material.
- Using personal context.
- Running data analysis on uploaded internal files.

### High Risk

- Reading or sending email.
- Calendar actions involving other people.
- Contact lookup and use.
- Handling private source material.
- Public claims.
- External communication.
- Publishing generated media.

## Required Connector Metadata

For future Orchestrator use, each ChatGPT connector operation should ideally expose:

- connector name,
- action name,
- target resource,
- read/write classification,
- approval requirement,
- security classification,
- result artifact,
- errors,
- elapsed time,
- user approval status,
- event stream entry.

## Operational Visibility Requirement

Connector use must be visible to the Office of the Steward when significant.

Examples:

- GitHub update started.
- GitHub file created.
- Connector blocked waiting for approval.
- Web research running.
- Email draft created.
- Calendar action awaiting confirmation.
- Repository write completed.
- Connector action failed.

The Steward should not have to infer connector activity from chat scrollback.

## Recommendation

ChatGPT connectors should be treated as powerful external-service adapters.

They should be governed by:

- routing policy,
- boundary policy,
- event emission,
- auditability,
- explicit approval for sensitive actions,
- Office of the Steward visibility.

The next implementation step should not be a monolithic ChatGPT adapter. It should be a small characterization harness that records ChatGPT-requested actions, connector outcomes, approval points, and artifacts into the Estate activity/event model.
