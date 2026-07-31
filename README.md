# ChatGPT Conversation Archive

Estate-wide local archive and incremental synchronizer. It is deliberately independent of any product or repository classification; optional downstream metadata can be added after export.

## Install and profile safety

From this directory run `npm install` and `npm run build`. Use the PowerShell initializer for first-time authentication. It starts an independent installed Chrome process with the dedicated profile and never enters credentials or copies cookies. Do not point it at a profile concurrently used by normal Chrome.

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

The installed launchers are independent of the PowerShell caller's current directory. If initialization reports `TS5058` for `tsconfig.json`, refresh the deployed installation so it contains `tsconfig.json`, `src`, and `dist`; do not run the launcher from the repository checkout as a workaround. Interactive initialization starts ordinary stable Chrome directly; Playwright is not involved in the login window. Complete login and any security challenge there, confirm the conversation interface is visible, then close that dedicated Chrome window and confirm the second console prompt. Only after Chrome exits does the archive runtime reopen the profile to verify authentication. Scheduled sync remains non-interactive and fails promptly with `AUTHENTICATION_REQUIRED`.

Initialization command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Initialize-ChatGPTConversationArchive.ps1`.

After successful initialization, the full archive command is `powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Run-ChatGPTConversationArchiveFull.ps1`.

The initializer identifies the dedicated session by enumerating Windows `chrome.exe` command lines for the normalized `--user-data-dir` profile path. It tolerates the initial launcher PID exiting during Chrome handoff, waits for the actual top-level window, and waits for the profile lock files to clear before verification.

Every archive run writes live progress and heartbeat state to `A:\AI\Archives\ChatGPT\status\current-run.json` and cumulative seat-aware runtime counters to `A:\AI\Archives\ChatGPT\state\runtime-metrics.json`. The console shows discovered/processed counts, the current conversation, heartbeat activity, and stall warnings. A browser-context loss stops the run and defers the remaining items instead of recording hundreds of false independent export failures; rerun `resume` after diagnosis.

### Throttling and pacing

The runtime detects rate-limit HTTP 429 responses and localized or changed wording around “Too many requests”, requests being too quick, and temporary conversation-access restrictions. It reports these as `RATE_LIMITED`, never as authentication or archive errors. Defaults are conservative: 1.5 seconds between conversation opens, 500 ms between pagination actions, an 8-action burst, and a 10-second burst cooldown. Faster settings can increase the chance of temporary account throttling.

The first throttle retry waits 5 minutes, then increases to 10, 20, and 30 minutes, with up to 30 seconds of jitter and a one-hour total retry window. These values are configurable in `config.example.json`. Completed exports and `state/run-state.json` are written before a throttle stop; rerun `resume` to continue without duplicating completed conversations. A retry-window exhaustion exits with status `RATE_LIMITED` and code 3. Interactive waits can be cancelled with Ctrl+C; completed work remains checkpointed.

### Interactive login troubleshooting

Interactive initialization uses `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe` as an ordinary independent process with the dedicated profile at `A:\AI\Tools\ChatGPTConversationArchive\profile`. Its arguments are `--user-data-dir`, `--window-size=1400,900`, `--window-position=50,50`, `--disable-extensions`, and `https://chatgpt.com/`. It has no Playwright defaults, remote-debugging pipe/port, automation control, cookie copying, or security-bypass behavior. The initializer verifies the effective Chrome process list and rejects forbidden automation or sandbox arguments.

The archive runtime uses Playwright only after the operator closes ordinary Chrome. If that post-login verification is blocked by Cloudflare or authentication, the command reports the failure; VPN, proxy, endpoint protection, privacy tooling, and DNS security must remain unchanged.

If Chrome remains on `Verifying you are human. This may take a few seconds.`, leave the legitimate verification page open and complete any challenge normally. Do not attempt to bypass or automate it. If normal Chrome login succeeds but archive-runtime verification later reports `LOGIN_VERIFICATION_INCOMPLETE`, that is an external authentication/browser-automation boundary; do not weaken VPN, proxy, endpoint protection, privacy tooling, or DNS security. Unattended full and sync commands do not wait for this prompt and continue to fail promptly with `AUTHENTICATION_REQUIRED` or `LOGIN_VERIFICATION_INCOMPLETE`.

## Archive and schema

The archive is `archive-manifest.json`, `state/conversation-index.json`, `conversations/<stable-id>/latest.*`, immutable `revisions/<revision-id>/`, `reports/<run-id>/`, and `logs/`. Canonical JSON is schema version `1.0`; each message preserves role and ordered content blocks, with source URL, optional timestamps, metadata, attachments, export completeness, limitations, and revision links.

Hashes exclude volatile `exportMetadata` and `revision` fields. A changed normalized conversation creates a new revision; unchanged content is skipped. Missing conversations are marked unavailable and never deleted. Writes use temporary files followed by rename.

## Limitations and selector maintenance

The live adapter depends on ChatGPT's accessible URL and `data-message-author-role` semantics, with a visible-article fallback. UI changes should be diagnosed with `diagnostics`, then selector logic in `src/browser.ts` should be updated and covered by `tests/fixture.spec.ts`. Long or virtualized history is traversed by bounded scrolling; attachments and branches are preserved only to the extent exposed in DOM metadata. Headed mode is recommended for the dedicated profile and unattended runs fail safely if authentication is unavailable.

## Privacy, recovery, uninstall

Archives and profiles contain sensitive conversation data and are excluded from Git. Never publish them or place credentials in config. If interrupted, rerun `resume`; successful revisions remain intact and the next report records failures. To relocate, copy the tool and set `archiveRoot`/`profilePath`; to uninstall, remove the neutral installation and configured archive only after preserving any required institutional record.
# ChatGPT Conversation Archive

The exporter inventories the history sidebar separately from the active conversation. It identifies the conversation scroll container by walking message-node ancestry, checking computed `overflow-y`, `scrollHeight > clientHeight`, visible bounds, and a measured `scrollTop` change. It then hydrates upward from the newest view until message count, first-message hash, scroll height, top position, loading state, and DOM node stability converge for four passes.

Completeness is evidence-based: `exportMetadata.complete` is true only for `completenessStatus: "complete"`. Safety ceilings produce `incomplete` or `timed-out`; they are never success. Virtualized DOMs are detected and records are accumulated and deduplicated by message id or role/content identity while preserving chronological order. Ctrl+C leaves the current item uncompleted and writes a cancellation checkpoint.

Use `config.example.json` as the conservative baseline. Bounded validation should precede any full run:

```powershell
& .\scripts\Run-ChatGPTConversationArchiveSync.ps1
```

The repaired full command is:

```powershell
& .\scripts\Run-ChatGPTConversationArchiveFull.ps1
```

Do not run the full command until a genuinely long conversation has passed bounded live validation.

Each completed conversation also receives `conversation.json`, `conversation.mhtml`, `conversation.pdf`, `validation.json`, and `manifest.json` under `conversations/<id>/`. PDF is generated from the complete canonical accumulated model, not a virtualized viewport.

Inventory completion requires the configured stable bottom passes (default 810), delayed-load dwell, and an upward/back-down probe. A partial scan is reported as incomplete and reconciled with the historical ID union. Stale running checkpoints are recorded under `state/recovered-runs/` and the interrupted conversation is requeued. Use `generate-artifacts --conversation-id <id>` for bounded artifact repair; do not use `full` or `resume` for bounded validation.
