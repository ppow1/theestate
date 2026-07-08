# Codex CLI Bridge Discovery - 2026-07-07

Status: Captured
Owner: Chief Architect / Steward
Classification: Estate Internal
Source Session: Codex CLI, multi-seat, and local worker bridge discovery

## Executive Summary

This session proved that Codex CLI can act as a programmatic execution surface for The Estate.

The key result was a working local AI to Codex to local AI loop:

```text
PowerShell/controller
-> Codex CLI via stdin
-> Codex result captured in memory
-> Ollama reviews result
-> clean PASS/FAIL returned
```

This means a local worker process can invoke Codex without browser automation, without the Steward copying prompts into the Codex web UI, and without manually pasting results back.

The capability is ahead of the expected roadmap and creates an immediate need for Ingrid/security review because Codex was given direct access to `A:\theestate` before the Estate has a formal Codex boundary policy.

## Repository and Environment Context

Repository:

```text
ppow1/theestate
```

Local repository path:

```text
A:\theestate
```

Codex CLI install method:

```powershell
npm install -g @openai/codex
```

Installed CLI version confirmed:

```text
codex-cli 0.142.5
```

Node/npm observed:

```text
node v24.13.1
npm 11.8.0
```

## Orientation Context

The worker session onboarded through the canonical Estate entry path:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Orientation_Handbook.md
docs/governance/Estate_Vision_and_Architecture.md
docs/governance/Estate_Manual.md
docs/governance/visuals/README.md
```

Relevant operating rules reinforced by the session:

```text
Local repo state is source of truth.
Use full executable PowerShell blocks.
Discovery before implementation.
Audit before completion.
Pat is final authority, not help desk.
Alfred coordinates; Alfred is not the whole Estate.
Ingrid owns boundaries/security.
```

## Parking Lot Update

A new Parking Lot item was added during the session.

File:

```text
operations/boards/parking_lot.md
```

Commit:

```text
2ac68f9dbc5d32f1af99b16689c7b6b7bed3c239
```

Item:

```text
PL-0025 - Role/task security classification should determine onboarding depth, so Ingrid can assign security levels appropriate to the role and work package; narrowly scoped workers receive bounded onboarding while higher-trust or broader-authority workers receive deeper governance, security, and institutional context.
```

## Codex CLI Installation Findings

The CLI installed successfully, but `codex` was not initially found on PATH.

npm global prefix observed:

```text
C:\Users\wille\AppData\Roaming\npm
```

Executable files observed:

```text
C:\Users\wille\AppData\Roaming\npm\codex
C:\Users\wille\AppData\Roaming\npm\codex.cmd
C:\Users\wille\AppData\Roaming\npm\codex.ps1
```

Temporary PATH fix:

```powershell
$env:Path = "C:\Users\wille\AppData\Roaming\npm;$env:Path"
```

Recommended permanent remediation:

```text
Add C:\Users\wille\AppData\Roaming\npm to the user PATH.
```

## Authentication Findings

`codex doctor` initially reported missing credentials.

After browser login, MFA, and phone verification, `codex doctor` reported:

```text
auth is configured
stored auth mode: chatgpt
stored API key: false
stored ChatGPT tokens: true
websocket connected
```

Important discovery:

```text
Codex CLI authenticates against a ChatGPT Business account and does not require API-key billing for this mode.
```

The account used in testing was:

```text
contact@ionoge.com (Business)
```

Phone verification accepted an already-used OpenAI phone number, which differed from the stricter GitHub MFA phone-number experience.

## Interactive CLI Fuel Gauge Findings

Inside the interactive Codex CLI, `/status` returned account, model, session, directory, context window, and usage-limit information.

Observed status fields included:

```text
Account: contact@ionoge.com (Business)
Model: gpt-5.5
Directory: A:\theestate
5h limit: 99% left
Weekly limit: 100% left
Context window: 99% left after a small task
Session ID present
```

Important discovery:

```text
/status is a usable CLI fuel gauge for authenticated seat usage.
```

This may allow the Estate to avoid browser scraping for basic Codex usage status.

## Interactive Slash Command Findings

`/help` was not recognized.

Typing `/` opened the command palette.

Observed commands:

```text
/model
/fast
/ide
/permissions
/keymap
/vim
/sandbox-add-read-dir
/experimental
```

Not observed:

```text
/clear
/cls
/reset
```

Implications:

```text
Fast mode exists and increases usage consumption.
Permissions are adjustable from CLI.
No obvious clear-screen command exists in the first-level command palette.
```

## Non-Interactive `codex exec` Findings

The following pattern succeeded:

```powershell
$prompt = 'Reply with exactly: hello from direct pipe'
$result = $prompt | codex exec -
```

Result captured:

```text
hello from direct pipe
```

Important discovery:

```text
codex exec accepts stdin and returns capturable stdout.
```

This proves a local controller process can invoke Codex without typing into the interactive TUI.

## Local AI to Codex to Local AI Loop

Final successful clean test:

```powershell
$prompt = "Reply with exactly: hello from clean bridge"
$result = $prompt | codex exec -

$reviewPrompt = @"
Did this Codex output contain exactly 'hello from clean bridge'?

Codex output:
$result

Return only PASS or FAIL.
"@

$review = $reviewPrompt | ollama run qwen2.5-coder:7b
$cleanReview = ($review -replace '\x1b\[[0-9;?]*[A-Za-z]', '').Trim()
```

Clean output:

```text
=== CODEX RESULT ===
hello from clean bridge

=== CLEAN LOCAL REVIEW ===
PASS
```

This proves:

```text
PowerShell/controller -> Codex CLI via stdin -> Codex result captured in memory -> Ollama reviews result -> clean PASS/FAIL returned
```

## Earlier File-Based Bridge Test

A disposable file-based bridge test used:

```text
runtime/codex_bridge_test/inbox
runtime/codex_bridge_test/outbox
```

The folders were created by the test script and were not expected to exist beforehand.

The local model generated an imperfect prompt:

```text
What is your name?
```

Codex responded:

```text
I’m Codex.
```

Local AI reviewed and returned:

```text
FAIL - Output does not match expected response.
```

Interpretation:

```text
The bridge worked; local model prompt discipline failed.
```

This supports using deterministic controller-built prompts for critical work rather than relying on a local model to invent exact prompts.

## Encoding and Terminal Noise Findings

Observed mojibake:

```text
IΓÇÖm Codex.
```

Expected text:

```text
I’m Codex.
```

Likely cause:

```text
UTF-8 / Windows console encoding mismatch.
```

Ollama also emitted spinner/control-character noise into terminal output.

Temporary cleanup used:

```powershell
$cleanReview = ($review -replace '\x1b\[[0-9;?]*[A-Za-z]', '').Trim()
```

Future bridge work must normalize encoding and strip terminal control characters before parsing.

## Codex Cloud Findings

`codex cloud --help` exposed:

```text
codex cloud exec
codex cloud status
codex cloud list
codex cloud apply
codex cloud diff
```

Initial `codex cloud list` returned:

```text
No tasks found.
```

Likely reason:

```text
The authenticated account contact@ionoge.com had no Cloud tasks yet.
```

The cloud commands were discovered but not fully characterized.

## Multi-Seat Implications

Plain CLI currently uses the default auth store:

```text
C:\Users\wille\.codex\auth.json
```

Probable multi-seat direction:

```text
C:\Users\wille\.codex-seat1
C:\Users\wille\.codex-seat2
C:\Users\wille\.codex-seat3
```

Selected by setting:

```powershell
$env:CODEX_HOME = "C:\Users\wille\.codex-seat3"
```

This has not yet been proven.

Fallback operating model remains acceptable:

```text
Use one authenticated seat until depleted.
Logout/login to the next seat.
Sequentially burn fixed-cost seat capacity.
```

## Budget and Resource Operations Implication

Pat confirmed the operating constraint:

```text
API budget is effectively zero.
Fixed-cost ChatGPT Business seats are preferred.
Additional API/token credits are not cost-effective for large projects.
```

Estate resource optimization should prioritize:

```text
maximum completed work packages per fixed monthly seat cost
```

not:

```text
maximum model quality or unconstrained API usage
```

The CLI bridge supports this strategy because ChatGPT-authenticated CLI usage draws from the same plan/seat limits rather than API-token billing.

## Security Sequencing Issue

Pat identified a sequencing concern:

```text
We jumped ahead of Ingrid.
```

Codex was given direct local access to `A:\theestate` before Ingrid had established the intended boundary layer governing what can go into and out of the Estate.

Current risk is manageable because the Estate is not yet at a highly content-sensitive state, but this must be remedied quickly.

Security implications:

```text
Ingrid must define what Codex can read/write.
Codex Bridge must support permission profiles.
Default access should not be unrestricted Estate access.
Boundary classification must precede routine use.
```

## Architectural Implication

Before this session:

```text
Steward manually copy/pasted between local workers, ChatGPT, Codex, and browser tabs.
```

After this session:

```text
Any local process that can launch a command and read stdout can invoke Codex.
```

Practical bridge pattern:

```text
Local Worker / Ollama / future Alfred
-> builds task prompt
-> pipes prompt to codex exec
-> captures result
-> evaluates/parses result
-> writes final artifact/audit log
```

This substantially reduces the need for browser automation as the first integration path.

## Recommended Next Institutional Step

Create and execute a bounded work package:

```text
WP-CODEX-CLI-001 - Codex CLI Bridge Characterization, Security Policy, and Integration Plan
```

Purpose:

```text
Institutionalize the Codex CLI discovery into a governed Estate capability.
```

The first version should remain investigative and policy/design oriented, not a broad production implementation.

## Milestone Statement

This session proved:

```text
Local AI can invoke Codex as a service.
```

That means Codex is no longer only a browser-operated tool. It can become an Estate-managed execution capability.