# ESTATE-OPS-001 / PR #509 Operator Failure Repair

## Scope

This report records the repair and operator-equivalent acceptance following the
first real Stream Deck test after PR #509. No new admin account was created,
no model was changed, and no institutional acceptance was granted.

## Verified failure cause

The operator profile in use was the installed Estate Operations v0.5 Plugin
profile, not the exported v0.4 legacy profile used by the earlier Codex
acceptance. Its com.estate.statusbridge plugin mapped WebUI start to:

A:\AI\Tools\EstateStreamDeckMVP\Core\Start-OpenWebUI.cmd

That path used the legacy Estate-Service-Lib.ps1, had no WebUI
double-press/open mapping, and reported health from generic HTTP/service
probes. The earlier Codex run therefore proved the canonical controller and a
legacy script invocation, but did not prove the active installed Stream Deck
plugin path.

The preserved live process evidence also showed stale status assumptions:

- the active manifest named the canonical database, but the recorded PIDs did
  not match the live processes;
- the live Gateway process was rooted in A:\theestate, not the canonical
  checkout;
- the live Open WebUI process had no DATA_DIR or DATABASE_URL in its
  environment;
- the operator consequently reached a first-run database despite the
  manifest reporting semantic validation.

Failure evidence was preserved before shutdown at:

A:\AI\Backups\Estate-Ops-001-PR509-Operator-Failure\20260731-220823

## Corrections

- Added canonical command entry points under scripts/ for WebUI open,
  WebUI stop, Estate core start/stop/restart, and environment clearing.
- Canonical start now passes explicit DATA_DIR, DATABASE_URL, and
  PYTHONPATH to the actual child process.
- Stop discovers canonical service owners on the configured ports, terminates
  their trees, waits for both ports to close, and records truthful stopped
  state.
- Status now revalidates live recorded PIDs, command identity, Gateway
  readiness, WebUI readiness, and persistent state instead of trusting a
  manifest or open port.
- Browser opening occurs only after semantic WebUI readiness.
- The installed v0.5 plugin was rebuilt/reloaded with canonical single,
  double, and long-press WebUI mappings. Its Runtime Status action now reads
  canonical controller status rather than generic port reachability.
- streamdeck_canonical_bindings.json now records the installed plugin
  mappings as well as the legacy compatibility bindings.

## Operator-equivalent acceptance

The installed profile was reloaded after plugin installation. The exact
operator command targets were invoked through the same .cmd paths used by the
plugin's detached cmd.exe /c call dispatch:

1. Canonical stop returned ports_closed=true; status was stopped,
   healthy=false, with ports 8080 and 11435 closed.
2. The WebUI double-press target started the canonical controller and issued
   the browser-open command only after WebUI readiness.
3. The live Open WebUI process and child both showed:
   DATA_DIR=A:\AI\OpenWebUI\EstateCanonicalData,
   DATABASE_URL=sqlite:///A:/AI/OpenWebUI/EstateCanonicalData/webui.db,
   and PYTHONPATH=A:\theestate-wp4233\src.
4. The selected database contained the approved admin, the
   estate/grace-grounded-test model, grace_runtime_bridge, and
   grace_runtime_grounding. No Create Admin Account state was introduced.
5. Canonical restart returned healthy=true with both semantic checks and
   live process identity valid.
6. Canonical stop again closed both ports and reported stopped.
7. Canonical full-core start returned state=running, processes=true,
   gateway=true, and webui=true.
8. A bounded authenticated Open WebUI request returned HTTP 200 and a
   truthful Grace response identifying the canonical Estate Gateway path.
9. A final stop/start repeat after the prior test process ended again produced
   stopped-then-running state, with both ports listening only under the
   canonical process records.

The browser-open action was issued by the operator target after readiness; no
manual provider or manually started Open WebUI process was used.

## Validation

- tests/test_canonical_webui_gateway_runtime.py: 7 passed.
- Added regression coverage for stale process records and wrong command
  identity.
- Python compilation passed.
- git diff --check passed.
- Canonical database quick check and expected-object checks passed.
- No live Qwen/Ollama call was made and no model was downloaded or changed.

## Preservation and next action

Qwen source/configuration, historical Qwen artifact/receipt, failed validation
evidence, the approved Open WebUI database backup, and all 16 stashes remain
preserved. A:\theestate was not modified by this repair.

PR #509 remains draft and unmerged. The exact next Steward action is to review
the pushed correction and the operator-equivalent evidence, then decide
whether PR #509 may be marked ready. Do not merge without explicit approval.
