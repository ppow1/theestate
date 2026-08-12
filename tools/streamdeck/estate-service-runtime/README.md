# Canonical Estate Stream Deck service runtime overlay

The complete historical MVP runtime is installed at
`A:\AI\Tools\EstateStreamDeckMVP`. The lifecycle files that are safety- and
status-critical are maintained in this repository under `Core`.

Use `Deploy-EstateServiceRuntime.ps1` to deploy this canonical overlay to the
workstation runtime. It updates only the explicitly listed governed lifecycle
files and does not touch service data, logs, state, databases, or unrelated
scripts.

The Stream Deck plugin source is maintained separately under
`tools/streamdeck/estate-status-bridge`. Build it from that directory with
`scripts/build.ps1`; install the resulting package only after validating the
manifest and tests.
