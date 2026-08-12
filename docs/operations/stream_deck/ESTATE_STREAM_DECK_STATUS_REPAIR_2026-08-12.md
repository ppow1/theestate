# Estate Stream Deck status repair

The canonical plugin source is
`tools/streamdeck/estate-status-bridge`. Its build script produces the local
plugin package; the installed copy under the user profile is a deployment
artifact, not an independent source tree.

The canonical service-runtime overlay is
`tools/streamdeck/estate-service-runtime`. Deploy it with its explicit overlay
script when the external MVP runtime needs to be refreshed.

Status behavior:

- governed service probes allow normal PowerShell startup overhead;
- per-service timeout/error results remain visible instead of becoming an
  unconditional aggregate `CORE 0/3`;
- CORE start schedules bounded convergence refreshes;
- SILLY status allows the measured P100 helper runtime while retaining UUID and
  no-fallback checks;
- action/probe/status transitions are written to a bounded rotating diagnostic
  log in the installed plugin directory.

GPU tiles resolve by the exact Estate physical resource UUID. GPU1 is the RTX
4090 UUID `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2`; GPU2 is the Tesla P100
UUID `GPU-6785b322-899d-8eec-e817-31d83279a414`. CUDA/runtime ordinals are
telemetry fields only and are never used as the tile identity.
