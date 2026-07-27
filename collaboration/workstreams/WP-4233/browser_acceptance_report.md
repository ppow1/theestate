# Browser/live acceptance report

The running local services were inspected after deployment. `estate/grace` was served by the restarted resident gateway with `toolIds=[grace_runtime_bridge]` and `filterIds=[grace_runtime_grounding]`; other resident model metadata contained neither association. The loopback Grace runtime returned healthy shadow-mode readiness, an explicit `NO_RECORD` current-objective result, and replay cursor 0.

The Open WebUI process was restarted through the Estate startup process. The exact browser transcript could not be captured from this non-browser execution surface; no browser result is represented as a pass. The Tool source was loaded and invoked directly through the installed Open WebUI-compatible module, and its runtime-unavailable path was tested.
