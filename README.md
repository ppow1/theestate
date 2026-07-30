# ChatGPT Conversation Archive

Estate-wide local archive and incremental synchronizer. It is deliberately independent of any product or repository classification; optional downstream metadata can be added after export.

## Install and profile safety

From this directory run `npm install` and `npm run build`. Run `node dist/cli.js init-profile --config config.example.json` once. This uses a dedicated persistent Chromium/Chrome profile and never enters credentials or copies cookies. Complete login interactively in that profile if prompted. Do not point it at a profile concurrently used by normal Chrome.

The intended neutral machine installation is `A:\AI\Tools\ChatGPTConversationArchive`; the repository copy is the source and the PowerShell scripts can be copied there by the operator. The example archive root is `A:\AI\Archives\ChatGPT`. Both are configurable.

## Commands

```text
node dist/cli.js full --config config.example.json
node dist/cli.js sync --config config.example.json
node dist/cli.js resume --config config.example.json
node dist/cli.js validate --config config.example.json
node dist/cli.js inventory --config config.example.json
node dist/cli.js diagnostics --config config.example.json
```

Routine Task Scheduler command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Run-ChatGPTConversationArchiveSync.ps1`.

## Archive and schema

The archive is `archive-manifest.json`, `state/conversation-index.json`, `conversations/<stable-id>/latest.*`, immutable `revisions/<revision-id>/`, `reports/<run-id>/`, and `logs/`. Canonical JSON is schema version `1.0`; each message preserves role and ordered content blocks, with source URL, optional timestamps, metadata, attachments, export completeness, limitations, and revision links.

Hashes exclude volatile `exportMetadata` and `revision` fields. A changed normalized conversation creates a new revision; unchanged content is skipped. Missing conversations are marked unavailable and never deleted. Writes use temporary files followed by rename.

## Limitations and selector maintenance

The live adapter depends on ChatGPT's accessible URL and `data-message-author-role` semantics, with a visible-article fallback. UI changes should be diagnosed with `diagnostics`, then selector logic in `src/browser.ts` should be updated and covered by `tests/fixture.spec.ts`. Long or virtualized history is traversed by bounded scrolling; attachments and branches are preserved only to the extent exposed in DOM metadata. Headed mode is recommended for the dedicated profile and unattended runs fail safely if authentication is unavailable.

## Privacy, recovery, uninstall

Archives and profiles contain sensitive conversation data and are excluded from Git. Never publish them or place credentials in config. If interrupted, rerun `resume`; successful revisions remain intact and the next report records failures. To relocate, copy the tool and set `archiveRoot`/`profilePath`; to uninstall, remove the neutral installation and configured archive only after preserving any required institutional record.
