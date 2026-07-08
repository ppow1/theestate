# ChatGPT Boundary Policy Draft

Status: Draft Boundary Policy  
Work Package: WP-CHATGPT-CLI-001  
Author: Chief Architect #6  
Classification: Estate Internal

## Purpose

This draft defines boundary expectations for ChatGPT use inside the Estate.

ChatGPT is powerful because it can combine Steward dialogue, repository context, web access, connector access, document generation, image generation, and planning. Those same capabilities require explicit boundary handling.

## Policy Summary

ChatGPT may be used for planning, governance, documentation, architecture, research, connector-backed context retrieval, and authorized repository maintenance.

ChatGPT should not receive unrestricted local Estate access, unrestricted private material, or uncontrolled authority to publish, send, execute, or promote work.

Sensitive connector use should be explicit, visible, auditable, and classified.

## Default Classification

Unless otherwise specified, ChatGPT work involving Estate internals should be treated as:

- Classification: Estate Internal

Material involving private Steward context, resident-private content, credentials, unreleased strategy, personal contacts, email, generated media, local runtime state, or high-trust material should default to a more restrictive classification.

## Data Classes

### Public

May be used with ChatGPT when useful.

Examples:

- public web documentation,
- public release notes,
- public product information,
- public GitHub repository material when applicable.

### Estate Internal

May be used with ChatGPT for authorized Estate work.

Examples:

- governance documents,
- architecture documents,
- work packages,
- non-sensitive repository context,
- internal planning notes.

### Restricted

Requires explicit need and boundary awareness.

Examples:

- security architecture,
- connector configuration,
- private operational state,
- sensitive local runtime details,
- unpublished policy decisions.

### Steward Only

Do not send to ChatGPT unless the Steward explicitly provides it for the task.

Examples:

- personal high-trust reflections,
- confidential personal material,
- Gray Man material,
- deep Confidant material,
- highly sensitive preference or identity context.

### Local Only

Should remain local unless explicitly promoted.

Examples:

- prompts,
- prompt history,
- generated media,
- local caches,
- credentials,
- secrets,
- raw runtime logs,
- local-only artifacts,
- unreviewed worker outputs.

## Connector-Specific Boundary Rules

### GitHub

Allowed for authorized repository work.

Risks:

- writing governance without review,
- treating GitHub as source of local runtime truth,
- publishing material before promotion,
- confusing commit with validation.

Policy:

- repository writes should be intentional and scoped,
- document changes should preserve governance hierarchy,
- implementation claims require audit or validation evidence,
- GitHub is an adapter, not the Communication Bus.

### Gmail

High boundary sensitivity.

Policy:

- read only when the task requires it,
- draft rather than send unless explicitly directed,
- do not expose private email content unnecessarily,
- treat outbound email as external communication.

### Calendar

Moderate to high boundary sensitivity.

Policy:

- schedule only when requested,
- avoid exposing private calendar details unnecessarily,
- external invitees require care.

### Contacts

Moderate to high boundary sensitivity.

Policy:

- use only for contact resolution or explicitly requested context,
- do not infer relationships beyond evidence.

### Web / Deep Research

Allowed for public current information and external research.

Policy:

- cite sources,
- distinguish public information from Estate authority,
- prefer official or primary sources for technical and policy claims,
- do not let web findings override Steward decision or Estate governance.

### Image Generation

Boundary sensitive.

Policy:

- generated resident, staff, or Steward-adjacent imagery should default to Local Only until intentionally promoted,
- do not publish generated media without promotion approval,
- screenshots of internal Office surfaces are Estate Internal or higher by default.

### Voice

Boundary sensitive for precision and privacy.

Policy:

- persist important conclusions into written artifacts,
- do not rely on voice transcript alone for canonical decisions,
- confirm critical implementation instructions in text.

### Memory / Personal Context

Useful but not authoritative.

Policy:

- memory may reduce repeated explanation,
- repository and governance remain stronger authority,
- do not treat personal context as permission to disclose or publish.

## Operational Visibility Requirements

Significant ChatGPT actions should eventually emit structured events visible to the Office of the Steward.

Examples:

- Planning Started
- Governance Draft Created
- GitHub File Read
- GitHub File Created
- GitHub File Updated
- Connector Waiting For Approval
- Boundary Review Required
- Work Package Drafted
- Implementation Handoff Created
- Validation Evidence Requested
- Result Returned

The Steward should not have to infer ChatGPT activity from chat scrollback alone.

## Approval Gates

Require explicit Steward approval or Boundary Office review for:

- sending email,
- creating calendar events involving others,
- publishing external statements,
- promoting Local Only or Restricted material,
- exposing private prompts or generated media,
- granting broad local filesystem access,
- enabling unattended execution,
- connecting ChatGPT to local execution paths,
- any action involving credentials or secrets.

## ChatGPT CLI Boundary Position

Future ChatGPT CLI integration should begin as a planning and artifact-generation provider, not an unrestricted executor.

Minimum expected constraints:

- explicit request envelope,
- assigned worker identity,
- classification field,
- allowed path list,
- output artifact path,
- event emission,
- no credential exposure,
- no unrestricted local writes,
- no outbound publication without promotion approval.

## Boundary Questions for Ingrid

Before institutionalizing ChatGPT CLI, Ingrid or the Privacy and Boundary Office should answer:

1. What classes of files may ChatGPT CLI read by default?
2. What files require explicit approval?
3. May ChatGPT CLI write directly to repository files, or only produce proposed artifacts?
4. What event details may be surfaced to the Office without leaking sensitive content?
5. How should prompts be classified and retained?
6. What local state must never be sent to external ChatGPT services?
7. What connectors require per-action approval?
8. How should session memory be handled for worker identity continuity?

## Recommended Initial Posture

For initial implementation:

- allow planning requests,
- allow governance and architecture drafting,
- allow bounded repository documentation updates through approved connectors,
- allow generation of work packages,
- prohibit unrestricted local execution,
- prohibit automatic outbound communication,
- prohibit automatic promotion of generated media or private artifacts,
- require event emission for significant work.

## Acceptance Standard

ChatGPT integration is not boundary-ready until it can demonstrate:

1. classified request intake,
2. explicit allowed scope,
3. visible activity state,
4. connector/action audit trail,
5. clear approval gates,
6. safe failure behavior,
7. boundary review for sensitive actions,
8. result artifacts that do not leak unauthorized material.
