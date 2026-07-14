# WP-0548 — Estate Stream Deck Status Bridge — Local CLI Build

## Status
Pending

## Objective

Build and install a minimal local Elgato Stream Deck plugin that provides live visual feedback for key Estate operational states.

This work package is specifically intended to be executed by **Codex CLI on the Steward's local Windows machine**, not Codex Web.

Codex CLI is expected to:

- clone or pull this work package from GitHub;
- execute from the local repository at `A:\theestate`;
- access the local `A:` drive;
- build the plugin locally;
- install or stage the plugin locally;
- leave the compiled artifact on the local machine even if GitHub cannot accept the binary package.

Do not treat GitHub as the delivery path for the compiled plugin.

---

## Repository

```text
A:\theestate
```

## Local build/output root

```text
A:\AI\Tools\EstateStreamDeckPlugin
```

## Existing Stream Deck control scripts

```text
A:\AI\Tools\EstateStreamDeckMVP
```

Required existing report scripts:

```text
01-Estate-Status.cmd
03-CueMastery-Status.cmd
05-WP-Pending.cmd
06-Validation-Status.cmd
07-Readiness-Status.cmd
17-Service-Health.cmd
```

---

## Scope

Create a plugin named:

```text
Estate Status Bridge
```

Initial supported actions:

1. Estate Repository Status
2. CueMastery Repository Status
3. Work Packages Pending
4. Validation Status
5. Operational Readiness Status
6. Estate Service Health

The first version is intentionally bounded. Do not add startup, shutdown, restart, Codex capacity gauges, resident controls, or profile generation in this work package.

---

## Functional behavior

### 1. Estate Repository Status

Repository:

```text
A:\theestate
```

Display states:

- green: clean and synchronized;
- yellow: dirty working tree;
- orange: behind upstream;
- blue: ahead of upstream;
- red: diverged or unavailable.

Compact key value examples:

```text
CLEAN
DIRTY
DOWN 1
UP 2
DIV
ERR
```

A single key press opens:

```text
A:\AI\Tools\EstateStreamDeckMVP\01-Estate-Status.cmd
```

### 2. CueMastery Repository Status

Repository:

```text
C:\Users\wille\Documents\GitHub\CueMastery
```

Use the same state rules as Estate Repository Status.

A single key press opens:

```text
A:\AI\Tools\EstateStreamDeckMVP\03-CueMastery-Status.cmd
```

### 3. Work Packages Pending

Preferred pending directory:

```text
A:\theestate\collaboration\work_packages\pending
```

Count Markdown work-package files.

Display states:

- green when count is 0;
- orange when count is greater than 0;
- red when the directory cannot be found or read.

Show the numeric count directly on the key.

A single key press opens:

```text
A:\AI\Tools\EstateStreamDeckMVP\05-WP-Pending.cmd
```

### 4. Validation Status

Use current repository/runtime evidence to determine validation posture.

At minimum distinguish:

- current / caught up;
- pending or behind count when discoverable;
- unavailable;
- malformed or error state.

Use green, yellow, and red states.

A single key press opens:

```text
A:\AI\Tools\EstateStreamDeckMVP\06-Validation-Status.cmd
```

Do not invent validation counts. If the repository does not expose a trustworthy merged-but-unvalidated count, display `UNK` or `N/A` and document the evidence gap.

### 5. Operational Readiness Status

Preferred readiness case directory:

```text
A:\theestate\runtime\operational_readiness\cases
```

Count open/non-final cases.

Display states:

- green when open count is 0;
- yellow when open count is greater than 0;
- red when the readiness source is unavailable or malformed.

A single key press opens:

```text
A:\AI\Tools\EstateStreamDeckMVP\07-Readiness-Status.cmd
```

### 6. Estate Service Health

Check these local services:

```text
Ollama             127.0.0.1:11434
Resident Gateway   127.0.0.1:11435
Office of Steward  127.0.0.1:8765
Open WebUI          127.0.0.1:8080
SillyTavern         127.0.0.1:8000
TextGen             one discovered port among 7860, 5000, 5005, 7861
```

Display:

```text
X/6
```

Color rules:

- green when all six are online;
- yellow when one to five are online;
- red when none are online or the status check fails completely.

A single key press opens:

```text
A:\AI\Tools\EstateStreamDeckMVP\17-Service-Health.cmd
```

---

## Polling and UI behavior

- Poll local status every 5 seconds.
- Update key title and/or key image through the Stream Deck plugin API.
- Polling must not open visible console windows.
- Polling must not invoke Git fetch every 5 seconds.
- Repository status polling should use local Git state and cached remote state; remote fetches may occur on a slower bounded interval such as every 5 minutes.
- Do not block the Stream Deck event loop.
- Recover cleanly from missing files, malformed JSON, stopped services, or unavailable repositories.

---

## Visual requirements

- large, high-contrast values readable from approximately 24 inches;
- no decorative watermark behind text;
- no tiny centered labels;
- dark background;
- strong state color border or background;
- compact titles only;
- distinguish actions by icon and color, not long text.

Suggested labels:

```text
EST
Q
WP
VAL
READY
HEALTH
```

---

## Implementation constraints

- Use the official Stream Deck plugin architecture and manifest format compatible with the installed Stream Deck software.
- Prefer JavaScript or TypeScript if supported by the installed official SDK/tooling.
- Keep runtime dependencies local.
- Do not require cloud services.
- Do not require GitHub at runtime.
- Do not require Python unless invoking an existing local script.
- Do not replace the existing Estate Operations profile in this work package.
- The plugin must expose six actions in the Stream Deck action list so the Steward can replace existing static status buttons with live plugin actions.

---

## Local build and artifact requirements

Codex CLI must build locally and write all build artifacts to:

```text
A:\AI\Tools\EstateStreamDeckPlugin
```

Required layout:

```text
A:\AI\Tools\EstateStreamDeckPlugin\src
A:\AI\Tools\EstateStreamDeckPlugin\dist
A:\AI\Tools\EstateStreamDeckPlugin\logs
A:\AI\Tools\EstateStreamDeckPlugin\BUILD_REPORT.md
A:\AI\Tools\EstateStreamDeckPlugin\TEST_REPORT.md
```

The final locally installable plugin package or plugin folder must be placed under:

```text
A:\AI\Tools\EstateStreamDeckPlugin\dist
```

If the official build creates a file such as `.streamDeckPlugin`, leave it in `dist`.

Do not stop with `binary files are unsupported`.

The compiled package is a **local build artifact** and does not need to be committed to GitHub.

---

## Repository deliverables

Commit only source-controlled material that belongs in the Estate repository, including:

```text
tools/streamdeck/estate-status-bridge/
```

Expected repository deliverables:

1. complete source code;
2. plugin manifest source;
3. build script;
4. local install script;
5. local uninstall script;
6. README;
7. source-level tests;
8. a completion receipt or implementation report.

Do not commit local machine paths as generated binaries. Local path defaults may be documented or configurable.

---

## Local deliverables

Required local deliverables under `A:\AI\Tools\EstateStreamDeckPlugin`:

1. built installable plugin artifact or installable plugin directory;
2. copied source snapshot if useful;
3. build logs;
4. `BUILD_REPORT.md`;
5. `TEST_REPORT.md`;
6. install script;
7. uninstall script.

---

## Installation and validation

Codex CLI must attempt the local installation rather than merely documenting it.

Validation requirements:

- confirm the plugin appears in Stream Deck;
- confirm all six actions appear in the action list;
- confirm each action updates its title or image from current local state;
- confirm each action opens its mapped detailed report when pressed;
- confirm polling produces no visible console windows;
- confirm the Stream Deck process remains responsive;
- confirm uninstall removes only this plugin;
- report exact output paths and SHA-256 hashes for built artifacts.

If Stream Deck must be restarted, Codex CLI may stop and restart it only after preserving the user's existing profiles and configuration. Do not delete or overwrite existing profiles.

---

## Evidence discipline

- Do not claim a status source exists unless verified locally.
- Do not invent validation debt or readiness counts.
- Mark unavailable metrics explicitly.
- Record discovered local Stream Deck version, SDK/tooling version, Node version, and build command.
- Preserve existing Stream Deck profiles.

---

## Completion report

At completion, report:

- repository commit SHA;
- repository source path;
- local build root;
- final plugin artifact path;
- plugin artifact SHA-256;
- installed plugin path;
- six-action validation table;
- any unavailable status source;
- whether Stream Deck restart was required;
- any remaining bounded follow-up.

---

## Codex CLI execution instruction

This work package is to be executed from a local Codex CLI session with access to `A:`.

The intended execution pattern is:

```text
1. Pull current main in A:\theestate.
2. Read this work package completely.
3. Implement repository source under tools/streamdeck/estate-status-bridge.
4. Build locally into A:\AI\Tools\EstateStreamDeckPlugin\dist.
5. Install and validate locally.
6. Commit source and reports to the working branch.
7. Leave binary build artifacts on A: even if they are not committed.
```

Do not redirect this work package to Codex Web.
