# ChatGPT Conversation Archive Browser-Control Boundary

The archive has two deliberately separate browser phases.

## Manual authentication

`Initialize-ChatGPTConversationArchive.ps1` starts the installed stable Chrome executable directly:

`C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`

It supplies only the dedicated `--user-data-dir`, normal window size and position, and `https://chatgpt.com/`. No Playwright launch, remote-debugging pipe or port, automation control, cookie transfer, credential handling, CAPTCHA handling, or security-control changes occur in this phase. The profile is `A:\AI\Tools\ChatGPTConversationArchive\profile` and remains separate from ordinary Chrome.

The operator completes authentication and legitimate security challenges in ordinary Chrome, confirms the conversation interface, closes the dedicated window, and confirms the console prompt. The initializer verifies that the independent process has exited before continuing.

## Archive runtime

Only after Chrome exits does `verify-auth`, full, sync, or resume invoke the archive runtime. Those operations may use Playwright to reopen the dedicated profile for DOM extraction and authentication verification. They must not wait for manual input. If the runtime cannot use the authenticated profile, it returns `AUTHENTICATION_REQUIRED` or `LOGIN_VERIFICATION_INCOMPLETE` and leaves VPN, proxy, endpoint protection, privacy tooling, and DNS security unchanged.

The manual Chrome command line is checked at runtime for Playwright control arguments (`--remote-debugging-pipe`, `--remote-debugging-port`) and sandbox-warning arguments (`--no-sandbox`, `--disable-setuid-sandbox`). Initialization fails if any appear.
