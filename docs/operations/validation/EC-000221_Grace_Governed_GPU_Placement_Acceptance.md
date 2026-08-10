# EC-000221 — Grace governed GPU placement acceptance

Status: **Blocked after one bounded visible task; no provider execution**  
Predecessor: `origin/feature/ec-000220-openwebui-auth-attention` at `0f209dd0de042245db985c85c9c17cbbfe8bfc57`  
Lane: `feature/ec-000221-grace-governed-gpu-placement`

## Profile continuity correction

The EC-000220/EC-000221 continuity defect was confirmed in the Playwright harness:
`defaultProfilePath()` was derived from `ROOT/runtime/browser/...`, so every isolated
worktree selected a different Chromium profile. The canonical resolver now uses:

`--profile` → `ESTATE_OPENWEBUI_PROFILE` → `%LOCALAPPDATA%\TheEstate\browser\openwebui-operator-profile`

The default symbolic profile identifier is `estate-openwebui-operator-profile`.
Both normal acceptance and `auth-bootstrap` call the same resolver. Evidence records
the symbolic identifier and persistence class only; cookies, databases, localStorage,
tokens, credentials, and absolute profile paths are not evidence.

The inactive EC-000220 profile was migrated once, without any owning Chromium process,
to the machine-local path. The prior profile remains intact. No profile contents are
tracked by Git and the accidental worktree `.webui_secret_key` is ignored.

Deterministic tests prove worktree-independent resolution, two-root equivalence,
CLI/environment precedence, outside-repository placement, shared auth-bootstrap and
acceptance resolution, symbolic evidence, and existing attention/privacy behavior.

## Candidate surface repair

The first EC-000221 candidate launch was not an Open WebUI frontend defect. It was a
server launch defect: Open WebUI was started directly from the EC-000221 worktree,
without the canonical controller environment. Its log recorded generation of a new
worktree-local `.webui_secret_key`; it therefore did not use the EC-000220 external
Open WebUI data directory, database, or secret.

Read-only HTTP probes showed the server and frontend were alive (`/`, `/auth`,
`/api/config`, and `/health` returned successfully; static assets returned 200), while
unauthenticated `/api/models` returned 401. The correction was to stop that candidate
and restart only the green candidate through the existing controller contract, using
the EC-000221 source root for Grace/Gateway and the existing external Open WebUI
state (`A:\AI\OpenWebUI\EstateCanonicalData`, its `webui.db`, and existing secret).
Production/canonical Open WebUI was not changed, accounts were not reset, and no
credentials were created.

The corrected candidate controller reported `validated`, `bridge_ready=true`, Grace
catalog present, and governed readiness enabled. Headed Playwright reached
`OPENWEBUI_READY` with Grace visible and the composer usable. Evidence:
`runtime/evidence/openwebui-operator/openwebui-operator-20260810010507681-a3558220`.

## GPU and lane evidence

Before dispatch, both Windows PnP devices were `OK` and `nvidia-smi` verified:

| Physical GPU | UUID | PCI bus | State |
|---|---|---|---|
| Tesla P100-PCIE-16GB | `GPU-6785b322-899d-8eec-e817-31d83279a414` | `00000000:04:00.0` | healthy, idle |
| NVIDIA GeForce RTX 4090 | `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` | `00000000:07:00.0` | healthy, 21.9 GiB free |

The existing 8192 MiB `qwen3:8b` floor selected only the RTX 4090 UUID and excluded
the P100. `qwen.local.text.4090` reported the same full UUID in its lane binding,
`CUDA_VISIBLE_DEVICES`, and compute resource identity. No P100 workload, stress,
benchmark, reset, reboot, or driver operation occurred.

## Single bounded task result

Exactly one bounded Grace task was submitted through visible Playwright using the
machine-local profile. The UI selected Grace and displayed the composer, but the
candidate returned `Model '' was not found`. The response was captured at:

`runtime/evidence/openwebui-operator/openwebui-operator-20260810010633934-fd967556`

The candidate log records that the browser payload contained `estate/grace`, then
the deployed Grace bridge attempted its configured `127.0.0.1:11435` endpoint while
the EC-000221 candidate Gateway was correctly listening on `11436`. That stale
active-slot bridge endpoint caused the downstream model resolution to collapse to
`Model ''`. No PTM/Helen/Engineering
reservation/Dispatch/adapter/provider receipt chain was created, no Qwen model was
loaded, and no provider execution occurred. Therefore allocation UUID == runtime
lane UUID == provider receipt UUID, Office Compute correlation, and Stream Deck
projection compatibility remain unproven. A second prompt was deliberately not sent.

After stopping only the EC-000221 candidate services and the 4090 lane, both GPUs
remained healthy: P100 9 MiB used/0% utilization and RTX 4090 2422 MiB used/8%
utilization; both retained their verified UUID and PCI identity.

This record preserves the blocked acceptance evidence and does not close PL-0042.
