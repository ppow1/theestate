# WP-4233 — Grace runtime tool bridge

This work package registers a read-only Open WebUI Tool and Grace-only grounding filter. The Tool calls the authenticated loopback `LoopbackGraceMomentumClient` boundary; it never reads runtime files and exposes no command or provider operation.

The Estate resident catalog associates `grace_runtime_bridge` and `grace_runtime_grounding` only with `estate/grace` through `info.meta.toolIds` and `filterIds`.
