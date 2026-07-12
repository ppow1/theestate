# WP-4040 Open WebUI Multi-Resident Gateway Integration Contract

This is staged, uninstalled work. It must not be represented as active gateway behavior.

A future active install may expose a controlled OpenAI-compatible model such as `estate/conference-room` or `estate/room/<room-id>` through the existing Estate resident gateway. Open WebUI remains a front end only; Estate runtime, resident identity, room membership, permissions, and transcripts remain authoritative inside the Estate.

## Required adapter behavior

- Preserve resident attribution in every multi-resident response.
- Carry `room_id`, `session_id`, and normalized target residents from Open WebUI metadata when provided.
- Support non-streaming and streaming OpenAI-style envelopes.
- Route all execution through the canonical resident gateway and approved multi-resident room core after installation review.
- Never execute privileged actions from chat-completion requests.
- Never auto-invite all residents or infer room consent from model availability.
- Keep staged status visible until active installation is deliberately performed.

## Known dependencies

- WP-4032 streaming compatibility.
- WP-4034 Ingrid gateway identity.
- WP-4035 Grace gateway exposure.
- WP-4038 Evelyn staged exposure when installed later.
- WP-4039 multi-resident conversation room core for actual room planning and turn execution.
