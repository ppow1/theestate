# WP-0520 - AI Services, Local Runtime, Search, and Command Palette Controls

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Replace AI-service placeholders and make cross-Office search and command navigation operational.

## Required Controls

- refresh local service and model inventory;
- start, stop, and restart approved local services through canonical service controls;
- load and unload supported models where implemented;
- inspect logs, failures, readiness, and provider state;
- search Office artifacts, personnel, work packages, and operational records;
- open search results directly;
- invoke only registered safe Office actions from the command palette;
- launch or route to Open WebUI and other approved local interfaces.

## Boundaries

Do not accept arbitrary shell commands, unrestricted Python handlers, or unregistered action IDs. Reuse existing service, provider, search, and command-palette runtimes. Do not create a second service registry or provider router.

## Functional Standard

Every retained control must call a canonical handler, produce legitimate state or durable evidence, refresh the Office, and report completed, blocked, or failed truthfully.

## Testing

Prove browser-to-handler-to-state-to-render behavior for inventory refresh, approved process control, model control where supported, logs, search, direct navigation, safe command invocation, and local-interface launch routing. Use fake service runners where needed.

## Acceptance Criteria

1. AI Services is not a placeholder page.
2. Approved local service controls work and persist truthful state.
3. Unsupported operations are specifically blocked rather than faked.
4. Search opens real results.
5. Command palette invokes only registered safe actions.
6. No arbitrary command execution is possible.
7. Focused tests and WP-0520 validation pass.

## Completion Receipt

```text
collaboration/work_packages/completions/WP-0520_codex_done.json
```

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0520_AI_Services_Local_Runtime_Search_and_Command_Palette_Controls.md and do exactly what it says.
```
