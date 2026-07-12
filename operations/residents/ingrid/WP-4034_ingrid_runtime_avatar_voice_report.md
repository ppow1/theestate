# WP-4034 Ingrid Runtime, Avatar, and Voice Report

Status: Staged for local runtime use  
Classification: Estate Internal  
Owner: Character Architecture / Resident Runtime

## Result

Ingrid is staged as a distinct Estate resident chat target through the OpenAI-compatible resident gateway model `estate/ingrid` and shared resident interaction framework.

## Runtime Surfaces

- Gateway model: `estate/ingrid`
- Resident surface: `operations/residents/surfaces/ingrid.json`
- Open WebUI export seed: `docs/residents/ingrid/platform-exports/openwebui-ingrid-v0_1.yaml`
- Boundary source: `docs/residents/ingrid/Ingrid_Boundary_Matrix_v0_1.json`

## Presentation Identity

- Avatar identity: `docs/residents/ingrid/Ingrid_Visual_Identity_v0_1.md`
- Voice identity: `docs/residents/ingrid/Ingrid_Voice_Identity_v0_1.md`

## Safety Notes

The chat surface is conversation-only for execution. Ingrid may advise on classifications, boundaries, connector safety, protected-source exclusions, and escalations, but the runtime does not execute privileged security actions or permission changes from chat.
