# PL-0036 — Comms8 Live Topology Reconsideration

Status: Captured
Priority: Strategic
Category: Estate Communications / Service Topology
Originator: Pat / Steward
Date Captured: 2026-08-06
Target Milestone: As Comms8 becomes more deeply integrated into the Estate ecosystem

## Idea

Reconsider the long-term Estate Comms8 deployment topology before the current Blue candidate route becomes the assumed permanent production architecture.

The current accepted candidate design keeps the authoritative Comms8 application and state on the Estate workstation. Public endpoints provide Internet-facing ingress, but authoritative operations traverse a reverse SSH tunnel back to the workstation notification proxy and Blue runtime. This remains acceptable for the current candidate phase because it preserves local control, avoids opening inbound workstation ports, and supports rapid candidate iteration.

For a future Live topology, investigate whether the authoritative Comms8 application and state should instead run directly on a public Estate-controlled server, leaving the reverse-tunnel route as a Blue/candidate, development, emergency, or administrative path rather than the normal Live data plane.

## Why It Is Parked

The current tunnel-backed candidate route is working and remains suitable for completing the present Comms8 integration and startup-reliability work. Separating or relocating the authoritative service now would create a new deployment project, expand scope, and interrupt the current acceptance campaign.

The architectural question becomes more important as Comms8 gains broader Estate responsibilities, stronger availability expectations, additional residents and workflows, or production-grade continuity requirements.

## Promotion Condition

Promote this item for architectural investigation when one or more of the following becomes true:

1. Comms8 is selected for sustained Live use beyond candidate validation.
2. Workstation availability, home-network availability, reverse-tunnel recovery, or startup ordering becomes an unacceptable Live dependency.
3. Additional Estate systems require Comms8 while the workstation is offline.
4. Live disaster recovery, redundancy, independent maintenance, or service-level expectations are defined.
5. The Steward intentionally opens a Blue-to-Live topology and state-hosting review.

The promoted investigation should compare at least:

- current tunnel-backed workstation Blue;
- server-local Live application and authoritative state;
- Blue/local candidate plus independent server-local Live;
- state migration, backup, rollback, credential, security, and operational ownership boundaries;
- whether any tunnel remains useful for development, administration, or emergency access.

## Explicit Non-Action

Do not relocate Comms8, create a new Live deployment, move authoritative state, alter DNS or routing, replace the reverse tunnel, or begin a topology-separation project merely because this item was captured.

Continue the current work to restore reliable SSH tunnel and startup behavior under the accepted candidate architecture. Promotion requires an intentional Steward decision.

## Related Evidence

- `docs/operations/reviews/ESTATE-COMMS8_Public_Endpoint_Tunnel_Dependency_Truth_Test_20260806.md`
- `docs/mcp/Estate_Comms8_MCP_App_Repair_and_Correct_Creation_Reference.md`
- Current truth-test finding: the legacy public endpoint directly depends on the reverse SSH tunnel; the PHP endpoint serves protocol discovery locally but delegates authoritative state operations through the same tunnel-dependent route.
- Current authoritative candidate state: `A:\theestate-data\candidate-blue-runtime`.
- Canonical Parking Lot process: `AI_COMMUNICATION_HINTS.md`.
