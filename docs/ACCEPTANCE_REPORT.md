# Acceptance Report — Estate-wide ChatGPT Conversation Archive

Date: 2026-07-30  
Repository: `ppow1/theestate`  
Branch: `work/chatgpt-conversation-archive`

## Implementation and installation

The implementation is under `tools/chatgpt-conversation-archive/` and is installed at:

`A:\AI\Tools\ChatGPTConversationArchive`

The configured neutral archive root is:

`A:\AI\Archives\ChatGPT`

The installation contains the compiled CLI, npm production dependencies, configuration example, package lock, and four operator PowerShell scripts. Archive output and browser-profile state are outside Git.

## Verification evidence

### Production launcher correction — 2026-07-30

The first operator initialization from `A:\theestate-wp4233` exposed a launcher deployment defect: the installed package did not contain `tsconfig.json`, and initialization consequently reported `TS5058` while running `npm run build`. All four PowerShell launchers now resolve the installation root from `$PSScriptRoot`, explicitly set that directory as the process location, validate required files, and pass absolute CLI/configuration paths. The deployed installation was refreshed with the complete TypeScript build inputs and compiled output.

Verification was performed from `A:\theestate-wp4233` for initialization, full, sync, and validate launchers. Initialization reached the expected manual-login boundary (`AUTHENTICATION_REQUIRED`) without the TypeScript path error; validation completed successfully. No credentials, cookies, or authentication bypass were automated.

Exact initialization command:

`powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Initialize-ChatGPTConversationArchive.ps1`

The operator should use the dedicated Chrome/Chromium window opened by the launcher, using the profile at `A:\AI\Tools\ChatGPTConversationArchive\profile`; do not use a normal concurrently running Chrome profile. After manual login, rerun the initialization command above, then run:

`powershell.exe -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Run-ChatGPTConversationArchiveSync.ps1`

The initialization flow keeps the dedicated browser open while the console displays `After login is complete in the dedicated browser, press Enter here to verify:`. Press Enter only after the conversation interface is visible. The CLI verifies authenticated state before reporting `Profile ready`. Browser closure or premature confirmation returns a nonzero actionable error. Normal full/sync runs do not use this prompt and continue to return `AUTHENTICATION_REQUIRED` promptly when unauthenticated.

The interactive authentication helper tests cover unauthenticated first run, browser availability during the manual-login wait, successful post-login verification, browser cancellation, and already-authenticated profiles. The launcher regression also verifies that non-interactive sync remains prompt-free and returns `AUTHENTICATION_REQUIRED` promptly.

### Interactive browser launch correction — 2026-07-30

Interactive initialization now prefers the installed stable Chrome executable. On the verification machine this resolves to `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`. It uses the dedicated persistent profile, a headed resizable 1400×900 window, viewport 1400×900, device scale factor 1, default browser zoom, and disabled extensions. The initializer retains only `--window-size=1400,900` and `--disable-extensions` as custom arguments; it adds no user-agent, stealth, cookie, JavaScript, sandbox, security, or CAPTCHA-bypass flags.

Cloudflare/browser verification is detected separately. If the page still presents human verification after the operator presses Enter, the result is `LOGIN_VERIFICATION_INCOMPLETE`, not a false authenticated success. The operator must complete the legitimate challenge in the dedicated Chrome window; no credentials, cookies, or security checks are automated.

### Live unresolved-defect correction — 2026-07-30

Live capture of the prior deployed build showed that Playwright injected `--no-sandbox` into the effective Chrome parent and child command lines despite the source custom-argument list not containing it. The corrected launch sets `chromiumSandbox: true`, excludes both `--no-sandbox` and `--disable-setuid-sandbox` from Playwright defaults, and asserts against every effective Chrome command line after launch. A corrected live launch produced zero forbidden sandbox arguments across six profile processes.

The profile contained `chatgpt.com` persisted zoom `-7.6035680338478615` and stale placement state. Initialization now repairs only `chatgpt.com`, `openai.com`, and `auth.openai.com` zoom records to Chrome's `zoom_level: 0` default and removes only `browser.window_placement`; it does not delete the profile or authentication data. Live verification observed the repaired origins at default 100% (no non-default origin zoom records) and measured the actual outer window at `left=50, top=50, width=1400, height=900`, with `maximized=false`.

The complete live effective parent command was:

```text
"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --disable-field-trial-config --disable-background-networking --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-back-forward-cache --disable-breakpad --disable-client-side-phishing-detection --disable-component-extensions-with-background-pages --disable-component-update --no-default-browser-check --disable-default-apps --disable-dev-shm-usage --disable-edgeupdater --disable-extensions --disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,BoundaryEventDispatchTracksNodeRemoval,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,BlockOriginHeaderModificationOnRedirect,Translate,AutoDeElevate,OptimizationHints,msForceBrowserSignIn,msEdgeUpdateLaunchServicesPreferredVersion --enable-features=CDPScreenshotNewSurface --allow-pre-commit-input --disable-hang-monitor --disable-ipc-flooding-protection --disable-popup-blocking --disable-prompt-on-repost --disable-renderer-backgrounding --disable-updater-scheduler --force-color-profile=srgb --metrics-recording-only --no-first-run --password-store=basic --use-mock-keychain --no-service-autorun --export-tagged-pdf --disable-search-engine-choice-screen --unsafely-disable-devtools-self-xss-warnings --edge-skip-compat-layer-relaunch --disable-infobars --disable-search-engine-choice-screen --disable-sync --enable-unsafe-swiftshader --window-size=1400,900 --window-position=50,50 --disable-extensions --user-data-dir=A:/AI/Tools/ChatGPTConversationArchive/profile --remote-debugging-pipe about:blank
```

It contained neither forbidden sandbox flag. The renderer retained the operating system's normal display scale (`--device-scale-factor=2` on this 4K machine); this is distinct from page zoom and was not artificially overridden.

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
| Unit tests | `npm test`: 3 files, 15 tests passed, including interactive authentication, browser configuration, and launcher regressions | Pass |
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
