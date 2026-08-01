# ESTATE-OPS-001 — Restore Canonical WebUI/Gateway Startup and Implement Real Blue/Green Control

## Objective

Restore the Estate Web UI and Resident Gateway to one canonical, reproducible startup chain and close the deployment-control failure identified in PR #508.

This package is authorized to correct startup control, state selection, semantic readiness, and Stream Deck integration. It is not authorization to redesign Grace, replace the Resident Gateway, upgrade Open WebUI, or alter resident/provider behavior beyond what is required to restore the existing approved Estate runtime.

## Verified incident facts

The startup-path audit established that:

- Stream Deck launches the legacy `Estate-Service-Control.ps1` path.
- Resident Gateway startup is rooted at `A:\theestate`, not the clean canonical worktree `A:\theestate-wp4233`.
- Open WebUI starts without explicit `DATA_DIR` or `DATABASE_URL`.
- Multiple competing Open WebUI databases exist.
- Startup success is based primarily on TCP port availability.
- No application blue/green selector, promotion record, or active-slot source of truth is in the actual service startup chain.
- OperatorDeck slot controls are window-placement controls only and must not be treated as deployment blue/green controls.
- Grace is served inside the Resident Gateway and has no independent startup process.

## Required outcome

After this package:

1. One canonical startup controller owns Open WebUI and Resident Gateway startup.
2. Stream Deck buttons invoke only that controller.
3. The intended Estate source root is explicit and recorded.
4. Open WebUI state selection is explicit and cannot silently fall back to a package-relative or installation-relative database.
5. Startup fails closed unless semantic readiness checks pass.
6. Active deployment slot, state/database identity, source commit, runtime version, and promotion metadata are durable and inspectable.
7. Blue/green controls govern the actual applications, not only desktop window placement.
8. A failed green candidate cannot replace the known-good active slot.
9. Rollback to the last known-good slot is explicit, tested, and documented.
10. The existing Grace/Open WebUI bridge and resident catalog are restored and validated through the canonical path.

## Safety boundaries

- Preserve `A:\theestate` and its existing uncommitted changes.
- Do not delete or overwrite any Open WebUI database.
- Before any state change, create timestamped backups of all candidate Open WebUI databases, WAL/SHM files, configuration, launcher state, and Stream Deck launch files.
- Do not upgrade Open WebUI from 0.10.2.
- Do not change installed local models.
- Do not download a model.
- Do not grant institutional acceptance.
- Do not merge the resulting PR.
- Stop and report if canonical source-root ownership cannot be determined from Estate authority records.

## Phase 1 — Reconcile the approved live baseline

Determine and record:

- canonical Estate source root for live Resident Gateway execution;
- canonical source commit;
- canonical Open WebUI installation root;
- canonical Open WebUI data directory and database;
- current approved administrator identity;
- expected Estate model aliases, tools, filters, functions, and associations;
- current Stream Deck profile and button action paths;
- installed runtime copies and synchronization requirements;
- current ports and service identities.

Use the July 31 audit report and current repository authority records. Do not infer that `A:\theestate-wp4233` is canonical merely because it is clean; prove the intended live root.

## Phase 2 — Recover and validate Open WebUI state

Select the approved canonical Open WebUI database only after read-only comparison of all candidates.

The selected state must pass:

- SQLite `PRAGMA quick_check`;
- expected administrator identity;
- expected Open WebUI schema/version compatibility;
- expected Estate integration objects or a documented bridge redeployment plan;
- no duplicate config-key startup failure;
- deterministic absolute `DATA_DIR` and/or `DATABASE_URL` binding.

Never start Open WebUI without an explicit approved state path.

## Phase 3 — Canonical service controller

Implement one authoritative service controller used by Stream Deck and operators.

It must:

- use explicit service manifests;
- set exact working directories;
- set exact environment variables;
- record requested executable and resolved executable;
- record source root and source commit;
- record state/database path and digest/identity metadata;
- reject unexpected inherited `DATA_DIR`, `DATABASE_URL`, `PYTHONPATH`, or root overrides;
- use process-identity checks, not only port checks;
- detect and reject unrelated processes already owning required ports;
- maintain truthful PID/status records derived from live process inspection;
- provide start, stop, restart, status, and health operations;
- retain bounded logs and startup evidence.

Remove the legacy direct startup path from active Stream Deck use, but preserve it until rollback acceptance is complete.

## Phase 4 — Semantic readiness

Resident Gateway readiness must verify at minimum:

- HTTP readiness on `127.0.0.1:11435`;
- expected server identity;
- `/v1/models` returns the approved resident catalog;
- `estate/grace` is present;
- expected Grace metadata/associations are present;
- source root and commit match the selected slot.

Open WebUI readiness must verify at minimum:

- HTTP readiness on `127.0.0.1:8080`;
- not in first-run administrator-creation state;
- approved administrator identity exists;
- selected database identity matches promotion metadata;
- expected Estate model/tool/filter/function objects and associations exist;
- Grace model path can be selected through Open WebUI;
- no startup exception or migration failure occurred after the port opened.

A listening port is not success.

## Phase 5 — Actual blue/green deployment control

Implement or complete application-level blue/green control for Gateway and Open WebUI.

The design must define:

- slot IDs (`blue`, `green` or existing canonical equivalents);
- immutable slot manifest containing source root, source commit, executable/runtime version, configuration digest, state/database reference, bridge deployment version, and validation status;
- one create-once promotion record identifying the active slot;
- candidate preparation without altering the active slot;
- pre-promotion validation;
- atomic or fail-closed promotion;
- post-promotion semantic validation;
- automatic or operator-authorized rollback to the last known-good slot;
- retained historical state and receipts;
- separation from OperatorDeck window-placement controls.

For Open WebUI, define whether application code may be blue/green while state remains one canonical shared database, or whether state snapshots are slot-bound. Choose one model explicitly and document migration/rollback consequences. Do not silently clone or diverge user state.

## Phase 6 — Stream Deck correction

Update the active Estate Operations Stream Deck actions so that:

- Gateway and Open WebUI buttons call only the canonical controller;
- button status reflects semantic health, not merely port state;
- active slot is displayed or available through status;
- failed starts display a truthful failure state;
- restart does not bypass slot selection;
- no button contains a stale hard-coded `A:\theestate` or package-relative database path unless that path is proven canonical;
- existing unrelated Stream Deck functions remain unchanged.

## Phase 7 — Bridge restoration

If the approved Open WebUI database does not contain current Estate bridge objects, use the canonical repository deployment tooling to restore:

- Grace Tool;
- Grace Filter;
- Estate model alias/association;
- required tool/filter/function associations.

Do not manufacture objects manually through SQLite. Use supported Open WebUI/runtime interfaces or the existing deployment script. Record created/updated object identities and prove idempotent redeployment.

## Phase 8 — Tests and live acceptance

Add automated tests covering:

- explicit state-path enforcement;
- rejection of missing/wrong database;
- rejection of first-run state;
- rejection of wrong source root/commit;
- rejection of unrelated port owner;
- Gateway semantic catalog validation;
- Grace presence validation;
- Open WebUI expected-object validation;
- stale PID-map repair;
- candidate-slot failure with active slot preserved;
- promotion and rollback;
- Stream Deck actions invoking the canonical controller;
- no confusion with OperatorDeck window slots;
- idempotent bridge deployment.

Then perform one controlled live acceptance:

1. Back up all state.
2. Start the approved active slot through the canonical Stream Deck/controller path.
3. Confirm Gateway semantic readiness.
4. Confirm Open WebUI semantic readiness.
5. Confirm Grace is visible/selectable.
6. Submit one harmless bounded Grace request through Open WebUI and verify the request reaches the Resident Gateway.
7. Stop and restart through Stream Deck.
8. Confirm the same state/database identity, administrator, Estate objects, active slot, and source commit remain selected.
9. Exercise a deliberately invalid candidate slot and prove the active slot remains available.
10. Exercise rollback without losing Open WebUI state.

Do not perform broad Engineering/provider testing in this package.

## Required documentation

Create:

- incident/failure analysis with timeline, direct cause, contributing causes, failed controls, detection gap, and corrective actions;
- canonical startup runbook;
- blue/green promotion and rollback runbook;
- Stream Deck operator note;
- state/database inventory and retention note;
- final implementation and live-acceptance report.

The failure analysis must explicitly state that the observed design did not place application blue/green control in the actual startup chain. Do not describe this as a blue/green mechanism that merely malfunctioned if the evidence shows it was never connected.

## Branch and PR

Create a fresh branch from current `main`:

`operations/canonical-webui-gateway-blue-green-repair`

Commit, push, and open a draft PR against `main`.

Do not merge.

## Completion criteria

- One authoritative startup path exists.
- Stream Deck uses it.
- Open WebUI data/state selection is explicit.
- Gateway source selection is explicit.
- Semantic health gates startup success.
- Real application slot/promotion metadata exists.
- Failed promotion leaves the active slot intact.
- Rollback is proven.
- Grace is visible and reachable through Open WebUI after restart.
- Database identity and Estate objects survive restart.
- Failure analysis is durable.
- All tests and live acceptance pass.
- `A:\theestate` pre-existing changes are preserved.
- Institutional acceptance remains ungranted.

## Final report

Report exact source roots, commits, executable paths, state/database paths, active slot, promotion record, Stream Deck actions, readiness checks, backup locations, bridge object identities, tests, live acceptance, rollback result, branch, commit, draft PR, preservation checks, and the exact next Steward action.
