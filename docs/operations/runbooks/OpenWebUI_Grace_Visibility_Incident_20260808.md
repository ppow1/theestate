# Open WebUI Grace visibility incident — 2026-08-08

## Result

The authenticated Open WebUI operator surface is usable. The canonical Grace
resident gateway is visible and selectable in the real model picker, and real
Grace conversations pass through Open WebUI. No database, Gateway, CME,
Comms8, or resident-runtime mutation was required.

## Evidence-backed boundary

The existing dedicated Playwright profile authenticated the existing admin
user. The canonical database contained both active records:

- `estate/grace` — the resident gateway surface selected by the UI;
- `estate/grace-grounded-test` — `Grace (Estate Resident Gateway)`, with base
  `estate/grace` and the governed tool/filter associations.

The authenticated `/api/models` catalog contained both records. Open WebUI
0.10.2 renders the resident-facing picker entry as `Grace` and routes the
conversation to `estate/grace`; the derived preset remains present in the
catalog and persistent state but is not rendered as a second duplicate picker
entry. This preserves the canonical deployment identity without creating a
duplicate Grace surface.

## Repair and validation

The acceptance defect was in the operator harness: it searched page text while
the model picker was closed, used a broad send fallback, and did not recognize
Open WebUI 0.10.2's `.chat-assistant` response container. The harness now opens
the semantic picker, confirms the selected-model control, uses the submit send
control, extracts assistant content from the actual assistant container, and
records authenticated catalog correlation.

The canonical Open WebUI process was restarted once using the existing bounded
restart helper. Only Open WebUI was restarted; `EstateCanonicalData`, Grace,
Resident Gateway, CME, and Comms8 were left intact.

Deterministic asset readiness returned 200 for `/`, `/static/loader.js`,
`/static/custom.css`, and `/static/splash.png`. Playwright readiness and doctor
returned `OPENWEBUI_READY`, with Grace visible and the composer usable.

## Live acceptance evidence

Successful detached runs are retained under `runtime/evidence/`:

- basic Grace round trip: `openwebui-operator-20260808130143738-f1567da0`;
- three-turn continuity: `openwebui-operator-20260808124759949-0d3680ec23`;
- authoritative CME grounding (`IDLE`):
  `openwebui-operator-20260808125025200-deffabb2`;
- action-provenance negative check:
  `openwebui-operator-20260808125600669-f1c8b8d475`;
- overlapping two-page conversations: detached run
  `cme-owner-20260808T125200664805Z-868833428e`;
- bounded failure evidence: detached run
  `cme-owner-20260808T130128448063Z-2e2da39c57`.

No credentials, cookies, authorization headers, or request bodies are written
to evidence.
