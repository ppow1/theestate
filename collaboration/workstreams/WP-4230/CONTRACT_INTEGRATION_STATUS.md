# WP-4230 Contract Integration Status

Governing package: `WP-4230_Open_WebUI_Grace_Conversational_Operations_Integration.md`.

Integration uses the existing Open WebUI resident extension seam and `openwebui_grace_operations.py` over an authenticated `GraceMomentumClient`. Discussion is non-mutating; inspection is read-only; mutation requires explicit approval. Canonical events alone render progress and event IDs suppress refresh/reconnect duplicates. Links target Estate objectives, directives, lifecycle, and Open WebUI conversations.

The adapter fails closed for unavailable/authentication/authority/malformed contract conditions. It imports no runtime persistence and invokes no provider. WP-4229 supplies replay, availability, lifecycle projection, control contract, and loopback transport contract at merged base `0fcb07b55cedc74d1b2dffe67f8218d3bcffc08c`. Production wiring uses `LoopbackGraceMomentumClient`; fixture tests use the published fake/client boundary.

Refresh consumes `health.healthy` and `readiness.ready` (including provider-effects-disabled and non-disabled mode) and rejects the legacy `availability.available` shape. Replay cursor and delivered event IDs are persisted only in an Open WebUI-owned checkpoint root (`runtime/openwebui/grace_momentum`, configurable for tests), never in Grace runtime persistence. Lifecycle projections and canonical event envelopes are rendered without inferring state from model text. Approval remains required for mutations; discussion and inspection are non-mutating. WP-4230 does not add transport, persistence, lifecycle, or provider behavior. Bounded-live readiness is not claimed; WP-4232 still owns dual-surface, shadow, and live acceptance.

Validation: the focused Open WebUI and shared contract command passes 21 tests. The larger campaign/resident aggregate was bounded and did not complete in the local window; no WP-4230 failure was observed in the focused suite.
