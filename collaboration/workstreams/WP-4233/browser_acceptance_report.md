# Browser/live acceptance report

## Runtime integration acceptance

The running local services were inspected after deployment. `estate/grace` is served by the resident gateway with `toolIds=[grace_runtime_bridge]` and `filterIds=[grace_runtime_grounding]`; other resident model metadata contains neither association.

Live Open WebUI browser validation was completed against the production `Grace` model and the temporary `Grace Grounded Test` model.

The following requests returned authoritative, un-paraphrased Grace Momentum runtime payloads through the complete Open WebUI path:

- `Use get_runtime_readiness. Return the complete tool result exactly as received.`
  - `source_operation=get_runtime_readiness`
  - `status=AUTHORITATIVE_RESULT`
  - runtime reported `ready=true` and `mode=shadow`
- `Use get_current_objective. Return the complete tool result exactly as received.`
  - `source_operation=get_current_objective`
  - `status=NO_RECORD`
  - reason `no_explicitly_active_objective`
- `Is there a current active objective?`
  - natural-language routing selected `get_current_objective`
  - the same authoritative `NO_RECORD` payload was returned without model paraphrasing

The authenticated Open WebUI API validation also passed for both required operations. The targeted regression suite completed with 24 passing tests.

These results close the Grace runtime integration defect: the deployment script now installs and associates both `grace_runtime_bridge` and `grace_runtime_grounding` with the Grace model, and the production browser path is verified end to end.

## Newly observed execution-orchestration gap

A separate live test requested a professional headshot of Evelyn for the Estate staff directory.

Grace responded that the request had been queued through Dispatch and routed to the Studio Adapter, assigned a Tier-2 visual-asset classification, and given an estimated preview time. No image was generated, no executable adapter invocation was evidenced, and no real queue or job identifier was returned.

This is not a failure of the completed Grace runtime-read integration. It is a distinct execution-orchestration capability gap: Grace can retrieve authoritative runtime state, but execution-oriented requests may still be narrated as completed handoffs instead of invoking a real capability adapter.

Required follow-on behavior:

- distinguish conversational requests, runtime-read requests, and execution requests;
- invoke the appropriate registered execution adapter for supported execution requests;
- return either the completed artifact or a real, durable job/queue identifier;
- prohibit invented dispatches, adapter claims, classifications, ETAs, and sign-off checkpoints when no corresponding runtime record exists.

The next engineering effort should address capability/adapter orchestration without reopening the validated WP-4233 runtime-read path unless new evidence contradicts this acceptance record.
