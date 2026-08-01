# ESTATE-OPS-001 Incident and Canonical Restoration

Date: 2026-07-31

Starting source commit: `22a276268fc25c4568954da84f6a4215c1b95c31`
Branch: `operations/canonical-webui-gateway-blue-green-repair`

## Incident timeline

1. The July 31 startup-path audit found Stream Deck actions calling the legacy
   `Estate-Service-Control.ps1` path.
2. That controller launched the Gateway from `A:\theestate`, launched Open
   WebUI without `DATA_DIR`/`DATABASE_URL`, and treated a listening port as
   success.
3. Open WebUI had competing databases: empty installation/package databases
   and a valid pre-redeploy database containing the approved administrator.
4. No application blue/green selector or promotion record was connected to
   service startup. OperatorDeck “slot” and “promotion” controls only moved
   windows.
5. This correction preserved all candidates, selected the valid state through
   read-only comparison, copied it logically into a new canonical state path,
   deployed the existing bridge through Open WebUI’s model layer, and connected
   Stream Deck to the canonical controller.

## Direct cause

The actual startup chain had no authoritative source/state selector and no
semantic readiness gate. It could report success for the wrong source checkout,
the wrong database, first-run state, or a process that had merely opened a
port.

## Contributing causes and detection gap

- Legacy and Core service controllers existed in parallel; the active buttons
  called the weaker legacy path.
- `A:\theestate` was hard-coded into the Gateway launcher while the current
  clean operational checkout was `A:\theestate-wp4233`.
- Open WebUI’s package-relative database default was not overridden.
- PID bookkeeping was stale and was not authoritative process identity.
- No application-level promotion record bound source commit, database identity,
  runtime version, and validation status.
- Health checks did not inspect the Gateway resident catalog or Open WebUI
  objects.

## Corrective controls

- `config/runtime/canonical_webui_gateway.json` is the explicit manifest for
  source root, executable paths, ports, state path, WebUI version, and shared
  state policy.
- `canonical_webui_gateway_runtime.py` rejects inherited root/state overrides,
  records source commit and state identity, requires semantic readiness, and
  writes durable slot/promotion evidence.
- Blue and green use isolated candidate ports (`11436`/`8081`); promotion
  revalidates the candidate, stops managed processes, starts the candidate on
  canonical public ports (`11435`/`8080`), and publishes promotion metadata only
  after post-promotion validation.
- Rollback returns to the last known-good validated slot and revalidates it.
- Stream Deck start, restart, status, Gateway, and WebUI actions now invoke the
  canonical controller. The legacy controller remains preserved for rollback
  review but is no longer on the active actions.
- Open WebUI uses one explicit shared database for both code slots. User state
  is not silently cloned or diverged.

## Boundary

This campaign did not upgrade Open WebUI, download or change models, modify
`A:\theestate`, or grant institutional acceptance. `institutional_acceptance_state`
in promotion evidence is `not_granted`.
