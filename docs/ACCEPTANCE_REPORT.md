# Acceptance Report — Estate-wide ChatGPT Conversation Archive

Date: 2026-07-30  
Repository: `ppow1/theestate`  
Branch: `work/chatgpt-conversation-archive`

## Completeness repair acceptance gate

The deployed fixed 30-wheel strategy was rejected: it scrolled the history sidebar and did not prove active conversation completeness. The repaired implementation uses measured containers, upward hydration, convergence, safety ceilings, virtualized accumulation, cancellation checkpoints, and completeness metadata. Full 325-conversation execution remains gated on bounded short, medium, and genuinely long live validation.

## Implementation and installation

The implementation is under `tools/chatgpt-conversation-archive/` and is installed at:

`A:\AI\Tools\ChatGPTConversationArchive`

The configured neutral archive root is:

`A:\AI\Archives\ChatGPT`

The installation contains the compiled CLI, npm production dependencies, configuration example, package lock, and four operator PowerShell scripts. Archive output and browser-profile state are outside Git.

## Verification evidence

### Production launcher correction — 2026-07-30

The first operator initialization from `A:\theestate-wp4233` exposed a launcher deployment defect: the installed package did not contain `tsconfig.json`, and initialization consequently reported `TS5058` while running `npm run build`. All four PowerShell launchers now resolve the installation root from `$PSScriptRoot`, explicitly set that directory as the process location, validate required files, and pass absolute CLI/configuration paths. The deployed installation was refreshed with the complete TypeScript build inputs and compiled output.

Verification was performed from `A:\theestate-wp4233` for initialization, full, sync, and validate launchers. The initializer now uses an independent stable Chrome process for manual login; archive-runtime verification occurs only after that process exits. No credentials, cookies, or authentication bypass were automated, and no VPN/proxy/endpoint/privacy/DNS security control was changed.

Exact initialization command:

`powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Initialize-ChatGPTConversationArchive.ps1`

The operator should use the dedicated stable Chrome window opened by the launcher, using the profile at `A:\AI\Tools\ChatGPTConversationArchive\profile`; do not use a normal concurrently running Chrome profile. Complete login, confirm the conversation interface, close that Chrome window, confirm the console prompt, and allow archive-runtime verification to run. After initialization succeeds, run:

`powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Run-ChatGPTConversationArchiveSync.ps1`

The initialization flow starts ordinary Chrome with no Playwright launch/control path. The console displays `When the ChatGPT conversation interface is visible, press Enter here`, then `Close the dedicated Chrome window now, then press Enter here for verification`. The script confirms Chrome has exited before invoking the archive runtime. Normal full/sync runs do not use either prompt and continue to return `AUTHENTICATION_REQUIRED` promptly when unauthenticated.

The tests cover the operator authentication handshake prompts, process-close detection, post-login verification command, independent Chrome arguments without Playwright control arguments, profile repair, and prompt-free non-interactive sync.

The initializer identifies the session by normalized `--user-data-dir` command lines rather than trusting the initial launcher PID, so a Chrome handoff is tolerated. It confirms the top-level dedicated window is gone and the profile locks are released before invoking the archive runtime.

### Exporter failure accounting and live progress correction — 2026-07-30

The historical 325-conversation run is classified from its observed error sequence as approximately: 1 primary exporter failure (`roleOf is not defined`), 1 browser-context loss, 324 cascading/deferred conversations, and 0 successfully processed. The corrected exporter defines the role mapping inside the browser callback, audits the remaining `evaluate`/`evaluateAll` calls for Node-scope references, stops on context loss, checkpoints the next item, and records the three categories separately.

Each run now emits console progress and periodic heartbeats, writes `A:\AI\Archives\ChatGPT\status\current-run.json`, and accumulates seat-aware counters in `A:\AI\Archives\ChatGPT\state\runtime-metrics.json`. A headed bounded live validation of one authenticated conversation completed successfully: 1 discovered, 1 processed, 0 failed, 0 context losses, 0 deferred, 856 requests, and 39 actions. The validation wrote status and metrics files under `A:\AI\Archives\ChatGPT-BoundedValidation-20260730-headed`. No throttle was induced.

### Throttle control correction — 2026-07-30

The archive runtime now detects modal/body throttle wording and HTTP 429 responses, emits `RATE_LIMITED`, applies 5/10/20/30-minute adaptive backoff with bounded jitter, and stops opening new conversations while limited. Pacing defaults are 1.5 seconds per conversation open, 500 ms per pagination action, 8-action bursts, and 10-second burst cooldowns. Checkpoints and reports preserve completed work and retry metrics; `resume` continues without duplicating completed exports. Mocked tests cover detection, backoff, cap/jitter, cancellation, and pacing. No live throttling was induced.

### Interactive browser launch correction — 2026-07-30

Interactive initialization now launches the installed stable Chrome directly, without Playwright. On the verification machine this is `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`. It uses the dedicated persistent profile and only `--user-data-dir`, `--window-size=1400,900`, `--window-position=50,50`, `--disable-extensions`, and the ChatGPT URL. It adds no remote debugging, user-agent, stealth, cookie, JavaScript, sandbox, security, or CAPTCHA-bypass flags.

Cloudflare/browser verification is detected separately. If the page still presents human verification after the operator presses Enter, the result is `LOGIN_VERIFICATION_INCOMPLETE`, not a false authenticated success. The operator must complete the legitimate challenge in the dedicated Chrome window; no credentials, cookies, or security checks are automated.

### Live unresolved-defect correction — 2026-07-30

Live capture of the prior deployed build showed that Playwright injected `--no-sandbox` into the effective Chrome parent and child command lines despite the source custom-argument list not containing it. The corrected launch sets `chromiumSandbox: true`, excludes both `--no-sandbox` and `--disable-setuid-sandbox` from Playwright defaults, and asserts against every effective Chrome command line after launch. A corrected live launch produced zero forbidden sandbox arguments across six profile processes.

The profile contained `chatgpt.com` persisted zoom `-7.6035680338478615` and stale placement state. Initialization now repairs only `chatgpt.com`, `openai.com`, and `auth.openai.com` zoom records to Chrome's `zoom_level: 0` default and removes only `browser.window_placement`; it does not delete the profile or authentication data. Live verification observed the repaired origins at default 100% (no non-default origin zoom records) and measured the actual outer window at `left=50, top=50, width=1400, height=900`, with `maximized=false`.

That Playwright-controlled launch path is no longer used for manual authentication. The current manual-login effective command line is:

```text
"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --user-data-dir=A:\AI\Tools\ChatGPTConversationArchive\profile --window-size=1400,900 --window-position=50,50 --disable-extensions https://chatgpt.com/
```

It contained no Playwright-generated arguments, no remote debugging argument, and no forbidden sandbox flag. The archive runtime is invoked only after this process exits; it does not control the manual-login window.

| Requirement | Evidence | Result |
|---|---|---|
| Estate-wide ownership and neutral naming | `tools/chatgpt-conversation-archive/`, root `README.md`, `docs/ARCHITECTURE.md`; no product filter or CueMastery path | Pass |
| Full, incremental, and resume modes | `src/sync.ts`, CLI commands `full`, `sync`, `resume` | Implemented |
| Stable identity and discovery | URL `/c/<id>` extraction, deduplicated manifest inventory, bounded scrolling | Implemented; live inventory blocked by authentication |
| Canonical JSON, Markdown, and HTML | `src/model.ts`, `src/storage.ts`, revision layout | Pass by source inspection and unit coverage |
| Hashing and revision preservation | deterministic recursive normalization excludes volatile export/revision fields; immutable revision directories | Pass |
| Atomic writes and checkpoints | temporary-file replacement, per-item index write, `state/run-state.json` | Pass by source inspection |
| Differential reports | JSON/Markdown summary and category files under `reports/<run-id>/` | Pass; live blocked report exists at `A:\AI\Archives\ChatGPT\reports\2026-07-30T15-13-52-257Z-7535834a` |
| Archive validation | installed `validate` command | Pass: `valid: true`, zero conversations, zero errors |
| Configuration and scheduling | `config.example.json`, CLI overrides, four operator scripts, Task Scheduler command in root `README.md` | Pass |
| Browser safety | dedicated persistent profile under neutral tool path; no credential automation or secret logging | Implemented; authentication initialization remains manual |
| Dependencies | `npm install` completed; 59 packages audited, 0 vulnerabilities | Pass |
| TypeScript build | `npm run build` | Pass |
| Unit tests | `npm test`: 4 files, 20 tests passed, including exporter callback audit, context-loss classification, heartbeat/stall warnings, seat-aware metrics, throttle detection/backoff/cancellation/pacing, and launcher regressions | Pass |
| Playwright integration fixture | `npm run playwright:test`: 1 test passed; pinned Chromium installed | Pass |
| CLI help | root and `validate --help` executed successfully | Pass |

## Live authenticated acceptance

The live test reached `https://chatgpt.com/` using the dedicated profile strategy, then correctly stopped with:

`AUTHENTICATION_REQUIRED: authenticate the dedicated Chrome profile, then retry`

The profile did not exist before initialization and no authenticated dedicated profile could be safely inferred. No password, cookie, token, or session secret was entered, copied, or written. Therefore the following live criteria remain externally blocked and are not claimed: real discovery, multiple-conversation export, long-conversation export, second-sync skip, controlled change detection, live interruption/resume, and live browser-safety acceptance. Once the Steward completes the one-time manual login in the dedicated profile, rerun `Initialize-ChatGPTConversationArchive.ps1`, then the routine sync and acceptance commands.

The unauthenticated full-run failure is actionable and nonzero; validation still succeeds and prior archive data is not removed.

## Known limitations

The extractor uses layered URL, accessible-role, durable-attribute, and visible-article selectors. Attachment metadata, alternate branches, and content not exposed by the live DOM are recorded only to the extent ChatGPT exposes them. Selector changes should be diagnosed with `diagnostics` and isolated in `src/browser.ts`. A manual login is required for first initialization; unattended runs fail safely when the dedicated profile is unavailable or unauthenticated.

## Final status

The implementation is built, tested, installed, and ready for manual profile initialization. Operational live validation is pending only the external authenticated-browser step above; this report deliberately does not claim that portion complete.
