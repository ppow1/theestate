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

The installed launchers are independent of the PowerShell caller's current directory. If initialization reports `TS5058` for `tsconfig.json`, refresh the deployed installation so it contains `tsconfig.json`, `src`, and `dist`; do not run the launcher from the repository checkout as a workaround. Initialization opens the dedicated profile and keeps it open while the console waits at `After login is complete in the dedicated browser, press Enter here to verify:`. Complete login and any security challenge in that dedicated window, confirm the conversation interface is visible, then press Enter in the console. The CLI verifies authentication before reporting success. Closing the browser or pressing Enter before login returns an actionable nonzero error; scheduled sync remains non-interactive and fails promptly with `AUTHENTICATION_REQUIRED`.

Initialization command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Initialize-ChatGPTConversationArchive.ps1`.

After successful initialization, the full archive command is `powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Run-ChatGPTConversationArchiveFull.ps1`.

### Interactive login troubleshooting

Interactive initialization uses the locally installed stable Google Chrome executable when available, the dedicated profile at `A:\AI\Tools\ChatGPTConversationArchive\profile`, and a real resizable 1400×900 outer desktop window. It leaves the browser's normal display scaling and page zoom in place, repairs targeted persisted zoom entries to the 100% default, and disables extensions for that dedicated profile. It does not use the operator's normal Chrome profile or copy cookies and credentials. The initializer-specific Chromium arguments are `--window-size=1400,900`, `--window-position=50,50`, and `--disable-extensions`; Playwright's generated `--no-sandbox` and `--disable-setuid-sandbox` defaults are explicitly excluded and Chromium sandboxing is enabled.

The initializer verifies the effective running Chrome command line and actual outer window bounds. If a forbidden sandbox argument is present or the window is not within the normal desktop-size range, initialization fails instead of reporting success.

If the browser remains on `Verifying you are human. This may take a few seconds.`, leave the legitimate verification page open and complete any challenge normally. Do not attempt to bypass or automate it. Press Enter in the console only after the ChatGPT conversation interface is visible. If the verification page remains active, initialization reports `LOGIN_VERIFICATION_INCOMPLETE`; close that dedicated window and retry later, or investigate normal Chrome/network/security conditions. Unattended full and sync commands do not wait for this prompt and continue to fail promptly with `AUTHENTICATION_REQUIRED` or `LOGIN_VERIFICATION_INCOMPLETE`.

## Archive and schema

The archive is `archive-manifest.json`, `state/conversation-index.json`, `conversations/<stable-id>/latest.*`, immutable `revisions/<revision-id>/`, `reports/<run-id>/`, and `logs/`. Canonical JSON is schema version `1.0`; each message preserves role and ordered content blocks, with source URL, optional timestamps, metadata, attachments, export completeness, limitations, and revision links.

Hashes exclude volatile `exportMetadata` and `revision` fields. A changed normalized conversation creates a new revision; unchanged content is skipped. Missing conversations are marked unavailable and never deleted. Writes use temporary files followed by rename.

## Limitations and selector maintenance

The live adapter depends on ChatGPT's accessible URL and `data-message-author-role` semantics, with a visible-article fallback. UI changes should be diagnosed with `diagnostics`, then selector logic in `src/browser.ts` should be updated and covered by `tests/fixture.spec.ts`. Long or virtualized history is traversed by bounded scrolling; attachments and branches are preserved only to the extent exposed in DOM metadata. Headed mode is recommended for the dedicated profile and unattended runs fail safely if authentication is unavailable.

## Privacy, recovery, uninstall

Archives and profiles contain sensitive conversation data and are excluded from Git. Never publish them or place credentials in config. If interrupted, rerun `resume`; successful revisions remain intact and the next report records failures. To relocate, copy the tool and set `archiveRoot`/`profilePath`; to uninstall, remove the neutral installation and configured archive only after preserving any required institutional record.
