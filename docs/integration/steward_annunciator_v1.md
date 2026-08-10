# Steward Attention Annunciator v1

The annunciator polls the existing `steward_attention.aggregate_attention()` result.
It writes `runtime/office/steward_annunciator.json`, a consumer-facing artifact with
active items, explicit severity, presentation history, and focus policy. The artifact
is suitable for a thin edge/corner renderer: consumers must not request keyboard or
mouse focus, and severity must be conveyed with text/icon/motion as well as any color.

Run a real Windows-local presentation with the host default audio endpoint:

```powershell
cd A:\theestate
PYTHONPATH=src python -m estate.cli.main steward-attention present --json
```

Use `--dry-run` for an entirely silent presentation test. The Windows adapter uses a
short `winsound.MessageBeep` and Windows `System.Speech` TTS; it does not estimate
Bluetooth distance or call a cloud service. Future Linux/KAMRUI and phone presenters
consume the same state/protocol and do not become attention authorities.

For explicit live acceptance, run this only from the signed-in interactive Windows
user session (it intentionally makes one sound and one utterance):

```powershell
cd A:\theestate
PYTHONPATH=src python -m estate.cli.main steward-attention live-test --text "The Estate needs your input on Project 5" --json
```

The result reports separate ding/TTS success, exceptions, stderr, and the session
context. Both mechanisms use the current interactive user's Windows default audio
endpoint; the presenter does not override endpoint selection.

`winsound.MessageBeep` returning `None` is normal for this Windows API and is not a
boolean audible-confirmation signal. The live command reports no exception for the
call, while TTS reports its PowerShell return code and stderr.

Safe offline demonstration:

```powershell
cd A:\theestate
PYTHONPATH=src python tools/demo_steward_annunciator.py
```

The demo injects a task-status condition, presents it once, polls it again without a
repeat, acknowledges through `record_action`, and confirms the visual state clears.
