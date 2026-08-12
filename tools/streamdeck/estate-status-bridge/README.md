# Estate Status Bridge

Local Stream Deck plugin source for WP-0548 and WP-0549.

The plugin exposes 17 actions matching the local Estate Operations profile layout:

- Estate Repository Status
- Estate Safe Sync
- CueMastery Repository Status
- CueMastery Safe Sync
- Work Packages Pending
- Validation Status
- Operational Readiness Status
- Estate Runtime Status
- Start Estate Surfaces
- Start Resident Gateway
- Start Office of Steward
- Start Open WebUI
- Start SillyTavern
- Start TextGen
- Stop Estate Surfaces
- Restart Estate Surfaces
- Estate Service Health

Runtime is dependency-free Node JavaScript using the Stream Deck SDK v2 manifest and WebSocket plugin process model. It polls every 5 seconds, uses hidden Git child processes for repository checks, uses filesystem reads for local Estate sources, and uses TCP sockets for localhost service health. Service health, runtime, and service control keys render segmented service-state bars.

Pressing any action launches the matching numbered command under:

```text
A:\AI\Tools\EstateStreamDeckMVP
```

## Build

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Default output root:

```text
A:\AI\Tools\EstateStreamDeckPlugin
```

The build creates:

```text
A:\AI\Tools\EstateStreamDeckPlugin\src
A:\AI\Tools\EstateStreamDeckPlugin\dist\com.estate.statusbridge.sdPlugin
A:\AI\Tools\EstateStreamDeckPlugin\dist\com.estate.statusbridge.streamDeckPlugin
A:\AI\Tools\EstateStreamDeckPlugin\dist\Estate Operations v0.5 Plugin.streamDeckProfile
A:\AI\Tools\EstateStreamDeckPlugin\logs\build.log
A:\AI\Tools\EstateStreamDeckPlugin\BUILD_REPORT.md
```

## Install

```powershell
powershell -ExecutionPolicy Bypass -File A:\AI\Tools\EstateStreamDeckPlugin\install.ps1
```

The installer copies only:

```text
%APPDATA%\Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin
```

Stream Deck may need a manual restart before the action list refreshes.

## Profile

The build generates an importable profile at:

```text
A:\AI\Tools\EstateStreamDeckPlugin\dist\Estate Operations v0.5 Plugin.streamDeckProfile
```

The generated profile uses plugin actions in the same positions recovered from `Estate Operations v0.4.streamDeckProfile`.

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File A:\AI\Tools\EstateStreamDeckPlugin\uninstall.ps1
```

The uninstaller removes only `com.estate.statusbridge.sdPlugin`.

## Tests

```powershell
npm test
```

## Validation Evidence Gap

The repository exposes latest validation and validation dashboard artifacts, but it does not expose a trustworthy merged-but-unvalidated debt count. The validation key therefore reports latest pass/fail/finding posture plus open observation/defect evidence, and uses `UNK` or `N/A` for unavailable or malformed sources.


