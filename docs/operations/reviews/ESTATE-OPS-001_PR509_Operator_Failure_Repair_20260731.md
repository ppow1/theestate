# ESTATE-OPS-001 / PR #509 Operator Failure Repair

## Scope

This report records the repair and operator-equivalent acceptance following the
first real Stream Deck test after PR #509. No new admin account was created,
no model was changed, and no institutional acceptance was granted.

## Verified failure cause

The cold-boot investigation corrected the earlier diagnosis. The active
installed profile is the Estate Operations v0.5 Plugin, and its loaded
`com.estate.statusbridge` action table maps WebUI single-press, double-press,
and long-press to the canonical files:

- `A:\theestate-wp4233\scripts\canonical_webui_gateway_webui_open.cmd`
- `A:\theestate-wp4233\scripts\canonical_webui_gateway_webui_stop.cmd`

The failure was at the `.cmd` boundary. `canonical_webui_gateway.cmd`
explicitly created empty `DATA_DIR` and `DATABASE_URL` variables before
invoking the Python controller. `load_config()` treated the mere presence of
those variables as an unsafe inherited override and exited before starting
either service. The detached Stream Deck `cmd.exe /c call` path therefore
looked like a successful launch to the operator while no WebUI was opened.

The earlier Codex acceptance reported success because it exercised the Python
controller/direct command path and/or observed a process already started by a
previous test. It did not execute the active plugin's detached `.cmd` boundary
from a stopped state, leaving this wrapper-only environment defect and the
browser-open behavior unproven.

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
- Canonical startup allows only inherited values that exactly match the
  canonical configuration and waits up to 120 seconds for cold-start semantic
  readiness, covering the initial Open WebUI embedding initialization.
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
- Operator-boundary start, browser-open, and stop events are appended to
  `Core/state/canonical-runtime/logs/operator-actions.jsonl`.

## 2026-08-01 cold-boot follow-up

The first post-restart double-press reached the operator wrapper but timed out
while Open WebUI performed its cold-start initialization. A subsequent
invocation through the same detached `cmd.exe /d /s /c call` path reached
semantic readiness, opened Edge at `http://127.0.0.1:8080/`, and recorded the
canonical data/database paths. The controller timeout is now 120 seconds so
this initialization is not reported as a silent operator failure.

The full operator control sequence then passed: WebUI stop, full-core start,
core restart, core stop with both ports closed, and a final full-core start
with `healthy=true`, `processes_match=true`, and both semantic readiness checks
true. The selected database still contains one approved admin and the Grace
model/tool/function objects; no Create Admin Account action occurred.

The authenticated Open WebUI-to-Grace request remains an explicit acceptance
boundary. Direct unauthenticated API probes correctly returned HTTP 401, and
no new account or credential was created. Therefore this follow-up does not
grant operator acceptance or mark PR #509 ready; a Steward-authenticated UI
request must still be observed in the existing session.

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
8. The authenticated Open WebUI request was not executed by Codex: this
   session has no safe browser automation surface for the established
   authenticated session, and no credential, cookie, or token was extracted.
   The required authenticated UI-to-Grace proof therefore remains open.
9. The runtime stop/start repeat was verified independently, with both ports
   listening only under the canonical process records.

The browser-open action was issued by the operator target after readiness in
the earlier operator-equivalent run; no manual provider or manually started
Open WebUI process was used. In the current authenticated-path attempt, the
Estate was started through the canonical core control path and is intentionally
left running for the Steward handoff below.

## Validation

- tests/test_canonical_webui_gateway_runtime.py and tests/test_wp4233_bridge.py:
  15 passed, including startup fail-closed coverage when Grace is unavailable.
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

## 2026-08-01 authenticated-path handoff

The current attempt began from stopped state and started the Estate through the
canonical core control path. Active slot blue is semantically ready for both
Gateway and Open WebUI. The actual Open WebUI listener is the expected
`open-webui.exe serve` process, and its live environment matches
`A:\AI\OpenWebUI\EstateCanonicalData` and the canonical `webui.db`. The
canonical database has one approved administrator and the expected
`estate/grace-grounded-test`, `grace_runtime_bridge`, and
`grace_runtime_grounding` objects. These checks are bounded and contain no
credentials or session material.

The browser must remain authenticated through the Steward's existing session.
Codex cannot safely drive that session from this environment, and direct
unauthenticated probes are not an acceptable substitute. The Estate is left
running. In the already authenticated normal WebUI, select
`estate/grace-grounded-test` and submit exactly:

> Grace, report your identity and confirm that this request reached you through the canonical Open WebUI and Resident Gateway path. Do not execute a provider task.

After submission, Codex must collect only bounded non-secret evidence: UTC
timestamps, approved non-secret user ID, conversation/request correlation,
selected model, tool/filter identities, Gateway/Grace correlation, HTTP/result
status, and a short visible-response summary. The collection must correlate the
authenticated WebUI request with the canonical WebUI chat/message rows and
Gateway/Grace logs; it must not read cookies, tokens, passwords, API keys, or
full secret-bearing payloads. The same bounded request must then be repeated
after the Steward closes the browser and uses canonical stop/start once more.

Until those two authenticated UI requests are durably correlated, this report
does not grant acceptance and PR #509 is not merge-ready.

## 2026-08-01 independent Grace runtime correction and acceptance

The prior correlation identified a real architectural omission: the canonical
PR #509 controller managed only Resident Gateway and Open WebUI, while the
accepted WP-4233 bridge contract independently requires the Grace Momentum
runtime on loopback port 8766. The Resident Gateway on 11435 is not that
runtime and was not substituted for it.

The correction adds the existing `scripts/run_grace_momentum_runtime.py`
entry point as a first-class managed service. Blue uses Grace 8766, Gateway
11435, and Open WebUI 8080; green uses 8767, 11436, and 8081. The controller
now authenticates its readiness probes, requires Grace health/readiness plus
persistence/replay/idempotency readiness, records all three process identities,
and fails closed when Grace is unavailable even if Gateway and WebUI are ready.
Stop, restart, status, promotion, rollback, manifests, and Stream Deck-equivalent
canonical start controls include all three services.

The complete authenticated operator sequence then passed twice. The first
post-correction request persisted conversation
`10120a3c-25c3-4dcd-ac17-5445a4ec5b2b` under the approved administrator with
`estate/grace-grounded-test`, `done=1`, and an
`AUTHORITATIVE_RESULT` from `grace-momentum-runtime`. Grace reported healthy
and ready in `governed_local_test` mode with its existing admitted state and
healthy persistence/replay/idempotency. The same conversation received a
second `done=1` authoritative result after canonical restart at
`2026-08-01T17:00:38Z`.

Open WebUI's configured local backend remained `http://127.0.0.1:11435/v1`,
and the live Gateway catalog returned `estate/grace` with the expected
`grace_runtime_bridge` and `grace_runtime_grounding` metadata. The persisted
Open WebUI custom model remained `estate/grace-grounded-test`, base
`estate/grace`, created and updated at `2026-08-01T00:54:00Z`; no model record
was altered during comparison.

After the browser was closed, canonical stop terminated all three managed
processes and closed 8766, 11435, and 8080. A final canonical start after that
complete stop returned validated readiness for all three surfaces. The
approved administrator and canonical database persisted; no account reset,
credential access, model download, or provider task was performed.

This is operational evidence only. PR #509 remains unmerged and is not being
marked ready or granted institutional acceptance.

The actual green candidate also validated on Grace 8767, Gateway 11436, and
Open WebUI 8081. Promotion to green and rollback to blue both completed with
three-service semantic validation; the final active record is blue with
`institutional_acceptance_state=not_granted`.

## 2026-08-01 authenticated-path correlation result

The Steward submitted the exact bounded message in the already authenticated
Open WebUI session. Read-only correlation found:

- WebUI persisted conversation `f6cf0efa-d134-4a31-b332-a6a86af6068c` under
  the approved administrator identity reference
  `1f0449c8-3564-4a9f-a344-a8de330302fe`.
- The selected model was `estate/grace-grounded-test`; the persisted model
  record remains associated with `estate/grace`,
  `grace_runtime_bridge`, and `grace_runtime_grounding`.
- The WebUI request completed with HTTP 200 and the assistant message was
  durably stored with `done=1`.
- The bounded bridge result was not a Grace success. Its source was
  `grace-momentum-runtime`, with `RUNTIME_UNAVAILABLE` and
  `control service unavailable` at 16:33:27.666238Z and 16:33:29.705095Z.
- The canonical Resident Gateway listener was present on 127.0.0.1:11435,
  but the bridge tool's configured default runtime endpoint is
  `http://127.0.0.1:8766`; no listener was present on 8766. The WebUI log
  confirms the tool module loaded and the authenticated chat endpoint returned
  200, but no corresponding successful Gateway/Grace result exists.

This proves the authenticated WebUI path and identifies the remaining repair:
the authoritative bridge/runtime boundary is miswired or not included in the
canonical service lifecycle. It does not prove a request reached Grace, so the
authenticated acceptance failed and PR #509 remains not merge-ready. No
credentials, cookies, tokens, API keys, or full secret-bearing payloads were
read or recorded. The Estate remains running for repair and re-test.

## 2026-08-01 final adversarial merge-readiness audit

The final audit began from reviewed head `6d2e425d5a6cc9e73f1a3bcccb984173adb8b1c2`.
It rechecked the complete three-service implementation, controller lifecycle,
slot manifests, promotion and rollback records, canonical Stream Deck binding
artifact, runbooks, incident reports, state inventory, and live acceptance
evidence. The required public surfaces are Grace Momentum `127.0.0.1:8766`,
Resident Gateway `127.0.0.1:11435`, and Open WebUI `127.0.0.1:8080`; candidate
surfaces are `8767`, `11436`, and `8081`. The source root is
`A:\theestate-wp4233` and the one persistent WebUI state is
`A:\AI\OpenWebUI\EstateCanonicalData\webui.db`.

During adversarial review, a live process set from before the final identity
hardening was semantically responsive but lacked the canonical Gateway
`--root` argument and explicit `ESTATE_ROOT`/database environment. The
reviewed status path correctly rejected that set (`processes_match=false`,
`healthy=false`) instead of accepting it. The correction makes controller
startup and status require canonical command identity and live environment
identity for Grace, Gateway, and WebUI; an old `A:\theestate` process,
stale PID, inherited process, unrelated port owner, wrong database, or first-run
WebUI therefore fails closed. The Gateway CLI now accepts and propagates the
canonical root used by the managed child.

The final focused validation passed 32 tests, including the Grace-unavailable
fail-closed regression, stale/foreign process identity rejection, and live
environment checks. Existing authenticated acceptance evidence remains bounded:
the approved administrator session, persisted conversation, selected
`estate/grace-grounded-test`, `grace_runtime_grounding`,
`grace_runtime_bridge`, `AUTHORITATIVE_RESULT` from `grace-momentum-runtime`,
Resident Gateway correlation, and a second successful turn after restart were
all recorded without credentials, cookies, tokens, or secret keys. The active
Stream Deck binding artifact invokes only the canonical controller and marks
the legacy controller inactive. Blue/green records preserve the same canonical
database identity; final institutional acceptance remains `not_granted`.

The final source-tree audit found no changed model or Open WebUI upgrade;
Open WebUI remains version `0.10.2`. `A:\theestate` was not modified by this
repair. PR #509 remains unmerged; after the hardening commit is pushed, this
report and the PR description are the merge-readiness record, not institutional
acceptance.
