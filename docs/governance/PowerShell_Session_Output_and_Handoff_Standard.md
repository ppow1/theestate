# PowerShell Session Output and Handoff Standard

Status: Canonical operating standard  
Owner: Steward / Chief Architect  
Audience: All AI workers, Chief Architect sessions, local CLI workers, documentation workers, and future operators

## Purpose

This standard defines how Estate workers should prepare PowerShell, diagnostic output, implementation handoffs, and iterative session results for Pat.

The goal is to optimize for:

```text
fast execution -> immediate review -> one-step paste back -> next action
```

It also prevents recurring interaction failures that create avoidable Steward frustration.

## 1. Console Initialization

Every PowerShell command block must begin with:

```powershell
CLS
```

`Clear-Host` is acceptable when appropriate, but `CLS` is the preferred default.

A clean console makes the resulting output easier to identify, review, and return.

## 2. Complete Executable Output, Not Fragments

Pat does not want disconnected code snippets that require manual assembly.

When PowerShell is requested, provide a complete executable block or a complete script suitable for direct use.

A normal command response should be structured as:

```text
Goal
Destination
Commands
Expected Result
```

When the work is meant to become reusable infrastructure, do not leave it as a chat-only snippet. Save the script in the correct repository or operational location and provide the exact execution command.

Do not require Pat to:

- combine fragments from multiple messages;
- infer missing variables or paths;
- manually add error handling;
- manually reconstruct output formatting;
- guess which working directory is required.

## 3. Output Capture

Whenever a script generates diagnostic information, inventories, reports, status, discovery results, or other information that Pat is expected to return to the model, the script should automatically copy the final report to the Windows clipboard whenever practical.

Preferred patterns:

```powershell
$Report |
    Out-String |
    Set-Clipboard
```

or:

```powershell
$Report = ...
$Report | Tee-Object -Variable DisplayReport | Out-String | Set-Clipboard
$DisplayReport
```

The final result must still be displayed in the console for local review.

The user experience should be:

```text
run script
review output
paste directly into ChatGPT
```

Do not force manual console selection when the script can safely place the final report on the clipboard.

## 4. Progress and Status Messages

Scripts should display concise, useful progress messages for operations that may take time.

At minimum, make clear:

- what is being inspected or changed;
- where output is being written;
- whether the command succeeded, failed, or completed with warnings;
- what the user should paste back or do next.

Avoid excessive noise that obscures the final report.

## 5. Human-Readable and Machine-Readable Results

Where practical, scripts should produce both:

- a clean human-readable console report;
- a durable JSON, JSONL, CSV, or Markdown artifact for later inspection.

Do not sacrifice readability merely to produce machine-readable output.

When diagnostics are intended for repeat use, write them to an appropriate Estate runtime, operations, reports, or tools path rather than only printing them.

## 6. Safe Interactive Diagnostics

Diagnostic and discovery scripts should be read-only unless the requested task explicitly requires a change.

They should:

- validate prerequisites;
- detect missing commands and paths;
- capture exit codes, stdout, stderr, and elapsed time;
- avoid submitting prompts or performing billable provider work unless explicitly authorized;
- distinguish observed fact from inference;
- stop safely on unsupported or dangerous operations.

## 7. Codex Handoff Timing

Do not provide a Codex handoff command before the work package exists in the repository.

A pre-creation handoff command is unusable and creates unnecessary noise.

The correct sequence is:

```text
1. Write the work package to GitHub.
2. Confirm the repository path and commit SHA.
3. Then provide the exact Codex handoff command.
```

The standard handoff format is:

```text
Read <repository-path> and do exactly what it says.
```

Example:

```text
Read collaboration/work_packages/pending/WP-XXXX_Example.md and do exactly what it says.
```

When a work package is actually created, always provide the handoff command automatically in the same completion response.

When a package has only been drafted and not written, explicitly say that it is not yet available and do not provide a misleading executable handoff.

## 8. GitHub Truthfulness

Never claim that a file, package, script, or document was written to GitHub unless the write succeeded.

After a successful write, provide:

- title or purpose;
- exact repository path;
- commit SHA;
- Codex handoff command when applicable.

If a connector or write fails, say so plainly and do not imply completion.

## 9. Reusable Script Placement

Choose the destination according to purpose:

```text
Repository diagnostics and Estate tooling:
A:\theestate\tools\diagnostics\

Estate operational scripts:
A:\theestate\tools\ or the existing subsystem path

AI-platform-wide scripts and services:
A:\AI\Scripts\ or the relevant A:\AI service directory
```

Prefer existing repository conventions over inventing new directories.

For scripts committed to the Estate repository, provide the repository-relative path and the local `A:\theestate` execution command.

## 10. PowerShell Quality Requirements

Complete scripts should normally include:

- `CLS` at the beginning;
- explicit working-directory handling when required;
- prerequisite checks;
- clear variable names;
- `try`/`catch` or equivalent error handling where failure is plausible;
- deterministic output paths;
- useful exit status;
- console display;
- clipboard copy for returnable reports;
- no destructive action without explicit authorization.

## 11. Session Interaction Preferences

Workers should remember:

- Pat prefers direct operational progress over repeated explanation.
- When Pat says `go`, proceed with the agreed action.
- Do not offer unusable commands before their target artifacts exist.
- Do not repeatedly ask for confirmation when the request is already clear.
- Do not substitute a plan for requested execution.
- Do not present decorative scaffolding as completed functionality.
- Do not call a report, button, page, or control operational unless it actually performs the intended function.
- Distinguish working, waiting, blocked, drafted, written, merged, and validated states accurately.

## 12. Guiding Principle

When generating PowerShell intended for interactive troubleshooting or collaboration, optimize for:

```text
fast execution
-> visible progress
-> clean final report
-> automatic clipboard capture
-> immediate paste back
```

When generating Estate work packages, optimize for:

```text
write first
-> confirm path and commit
-> provide Codex handoff
-> inspect real implementation results
```

These are required operating behaviors, not optional stylistic preferences.
