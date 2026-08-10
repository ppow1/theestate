# WP-4214 Steward Attention Annunciator v1 Validation Report

## Result

Implemented a local presenter boundary over the canonical Steward attention service.
Durable state is written to `runtime/office/steward_annunciator.json`; it is a
presentation artifact and not an authority, router, queue, or event bus.

## Validation

- `PYTHONPATH=src python -m pytest -q tests/test_steward_attention.py tests/test_steward_annunciator.py tests/test_steward_attention_office_integration.py` — passed (11 tests).
- `PYTHONPATH=src python tools/demo_steward_annunciator.py` — passed; one mocked presentation, repeat suppressed, acknowledgement cleared state.
- `PYTHONPATH=src python -m estate.cli.main steward-attention present --dry-run --json` — passed without real sound/TTS.
- `PYTHONPATH=src python -m py_compile src/estate/core/steward_annunciator.py tools/demo_steward_annunciator.py` — passed.

## Boundary Checks

The Windows adapter is isolated behind `Presenter.announce`, uses local MessageBeep
and Windows System.Speech on the default endpoint, and has no cloud dependency.
Failure leaves the visual alarm active and retries on the next poll. Existing Office
attention actions remain the only clearing mechanism; acknowledged, delegated,
dismissed, resolved, and snoozed items are not active annunciator items.

The original offline demo intentionally used `DemoPresenter`, so it was never
supposed to emit sound. Its clear assertion now reports `cleared_active: true` when
the underlying attention action has cleared the annunciator.

## Live acceptance evidence

- Interactive context: user `wille`, Windows ConsoleHost, active console session 1;
  not session 0/service context.
- Ding: success. Mechanism was `winsound.MessageBeep` with
  `MB_ICONEXCLAMATION`; Python returned `None` and raised no exception.
- TTS: success. Mechanism was Windows PowerShell `System.Speech.Synthesis.SpeechSynthesizer.Speak`;
  process return code 0, stdout empty, stderr empty.
- Endpoint: neither API accepts an endpoint override here; both use the current
  interactive user's Windows default playback endpoint. The presenter could not
  resolve the selected endpoint name. PnP enumeration did show available endpoints,
  including `Speakers (Logi USB Headset)` and several Voicemeeter/headset endpoints.
- Isolated live activation: one item presented (`new_item_count: 1`,
  `presented_count: 1`), existing `acknowledge` action recorded, and durable state
  verified `active: false` with no active item IDs.

## End-to-end operational slice

The real source is the existing `resident_task_visibility` projection consumed by
`steward_attention.aggregate_attention()`. Start the user-session poller with:

```powershell
cd A:\theestate
$env:PYTHONPATH="src"
python -m estate.cli.main steward-attention watch --interval 15
```

The existing Operations Center server then consumes the durable annunciator state.
Its fixed corner banner and Steward Attention tab are remote-safe consumers of local
Estate artifacts; the banner does not auto-focus or steal keyboard focus. Clicking
`Acknowledge` posts to the existing `/api/office/actions/execute` endpoint using
`attention.acknowledge`, which invokes canonical `record_action(..., "acknowledge")`.
The served endpoint was exercised in focused tests over HTTP; no browser-local or
Windows-only state is required to render the banner.

The existing `launch_operations_center.ps1` now starts the watcher as a hidden
interactive-user companion and stops it with `-Stop`; no new Windows service or
notification runtime was introduced.
