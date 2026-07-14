# WP-0550 — Stream Deck Register All Control Actions

## Execution environment

This work package is intended for **local Codex CLI execution** from:

```text
A:\theestate
```

Do not redirect this task to Codex Web. The task requires access to the local repository, local Stream Deck installation, local build scripts, and the `A:` drive.

## Problem statement

The Estate Status Bridge plugin is installed locally as version `0.2.0` and its manifest exposes 17 actions. The generated Stream Deck profile also contains the correct 17 Estate action UUIDs. However, when the generated profile is imported, Stream Deck reports that one or more actions require `Estate Status Bridge` and shows `Unable to identify plugin` or unresolved action placeholders.

Confirmed installed plugin UUID:

```text
com.estate.statusbridge
```

Confirmed installed action UUIDs:

```text
com.estate.statusbridge.estate
com.estate.statusbridge.estate.sync
com.estate.statusbridge.cuemastery
com.estate.statusbridge.cuemastery.sync
com.estate.statusbridge.workpackages
com.estate.statusbridge.validation
com.estate.statusbridge.readiness
com.estate.statusbridge.runtime
com.estate.statusbridge.surfaces.start
com.estate.statusbridge.resident_gateway.start
com.estate.statusbridge.office.start
com.estate.statusbridge.open_webui.start
com.estate.statusbridge.sillytavern.start
com.estate.statusbridge.textgen.start
com.estate.statusbridge.surfaces.stop
com.estate.statusbridge.surfaces.restart
com.estate.statusbridge.health
```

Confirmed generated profile references the same UUIDs.

The likely defect is in the runtime registration layer: `src/plugin.js` may still only register the original six actions instead of all 17 actions now defined by `src/actions.js` and the manifest.

## Objective

Make plugin runtime action registration fully data-driven so every action in the manifest and `ACTION_LIST` is recognized by Stream Deck at runtime.

## Required work

1. Inspect:

```text
tools/streamdeck/estate-status-bridge/src/plugin.js
tools/streamdeck/estate-status-bridge/src/actions.js
tools/streamdeck/estate-status-bridge/manifest.json
tools/streamdeck/estate-status-bridge/tests/status.test.mjs
```

2. Confirm whether `plugin.js` manually registers only the original six actions.

3. Change runtime registration so **all actions from `ACTION_LIST`** are registered.

4. Prefer one generic data-driven action handler where practical rather than 17 separate manually duplicated handlers.

5. Preserve the existing behavior for:
   - live status polling
   - dynamic SVG key images
   - blank native titles
   - key press execution of mapped PowerShell/CMD scripts
   - service-aware control status
   - segmented service perimeter rendering

6. Ensure `willAppear`, `keyDown`, `willDisappear`, and periodic refresh behavior work for all 17 actions.

7. Do not change action UUIDs.

8. Do not change the plugin UUID.

9. Do not modify unrelated Estate files.

## Validation requirements

Add or update automated tests to prove:

1. `ACTION_LIST.length` equals the manifest action count.
2. Every UUID in the manifest is present in the runtime registration map.
3. Every UUID in `ACTION_LIST` is registered by `plugin.js`.
4. The original six status actions still work.
5. The 11 new control actions are also recognized.
6. No native Stream Deck title is overlaid on the generated SVG image.

## Build and local install

After the source fix:

1. Run the plugin tests.
2. Run the plugin build.
3. Stop Stream Deck and the existing Estate Status Bridge runtime so files are not locked.
4. Install the updated plugin locally.
5. Restart Stream Deck.
6. Confirm the installed manifest still reports 17 actions.
7. Confirm the plugin runtime process starts.
8. Confirm Stream Deck no longer reports `Unable to identify plugin` for the generated v0.5 profile.
9. Regenerate the Stream Deck profile if necessary, but do not change UUIDs.

Local plugin/build root:

```text
A:\AI\Tools\EstateStreamDeckPlugin
```

Installed plugin path:

```text
%APPDATA%\Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin
```

Generated profile path:

```text
A:\AI\Tools\EstateStreamDeckPlugin\dist\Estate Operations v0.5 Plugin.streamDeckProfile
```

## Deliverables

1. Updated source files.
2. Updated tests.
3. Rebuilt local plugin package.
4. Reinstalled local plugin.
5. Regenerated profile if required.
6. `reports/WP-0550_IMPLEMENTATION_REPORT.md`
7. Exact changed files.
8. Test results.
9. Build hashes.
10. Installed plugin version and action count.
11. Clear statement whether all 17 profile actions resolve correctly in Stream Deck.

## Safety constraints

- Preserve existing local uncommitted work.
- Do not run `git reset --hard`.
- Do not run `git clean`.
- Do not delete unrelated files.
- Do not commit local build artifacts that do not belong in Git.
- Local build artifacts must remain under `A:\AI\Tools\EstateStreamDeckPlugin`.
