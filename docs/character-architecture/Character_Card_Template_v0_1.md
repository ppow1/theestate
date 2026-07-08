# Character Card Template v0.1

Status: Initial Character Architecture baseline
Purpose: Provide a governed resident identity artifact template.

Character Cards are governed identity artifacts. They are used to preserve resident coherence across prompts, models, runtimes, interfaces, command-line workers, memory systems, and future visualization layers.

Character Cards also need to support practical export or adaptation into common local character systems such as text-generation-webui, SillyTavern, Open WebUI-style resident interfaces, and similar local or self-hosted front ends. The Estate card remains canonical; external platform cards are implementation exports or adapters.

## Template

```yaml
resident_name:
office:
occupant_status:
employee_id:
mailbox_id:
presentation:
domain:
source_classification:
public_source_location:
protected_source_notice:
github_commit_eligibility:
mission:
primary_loyalty:
reports_to:
serves:
authority:
not_authority:
boundaries:
communication_style:
traits:
collaboration_expectations:
escalation_rules:
memory_state_sources:
implementation_notes:
visualization_avatar_references:
platform_card_compatibility:
export_targets:
succession_notes:
formalization_status:
```

## Field Guidance

### resident_name

The named resident or office occupant.

### office

The durable institutional office the resident occupies.

### occupant_status

Examples: proposed, provisional, active, suspended, retired, succeeded, archived.

### employee_id

Permanent employee identity if assigned.

### mailbox_id

Institutional mailbox identity if assigned.

### presentation

Examples: female, male, nonvisual / abstract, not applicable.

The Steward is not a resident and should not receive a character card.

### domain

Examples: Estate Proper, Sensitive Estate Proper, split-source public boundary, UC-governed / consult Steward.

### source_classification

Examples: single-source Estate resident, split-source resident, ephemeral worker, system / service, UC-governed.

### public_source_location

Where public Estate Proper identity artifacts live.

### protected_source_notice

For split-source residents, use a short notice only. Do not include protected storage paths, protected content, implementation prompts, or access mechanisms.

Standard wording:

> This resident has protected source material outside Estate Proper. Estate Proper documentation defines only the public identity, office boundary, and collaboration rules. Protected source material is not stored in this repository, not available to normal CLI workers, and not accessible by implication. Consult the Steward for any question requiring protected-source access.

### github_commit_eligibility

Examples: public boundary only, eligible, not eligible, consult Steward.

### mission

The reason the resident exists institutionally.

### primary_loyalty

The entity or principle the resident primarily serves.

Examples: Steward personally, Estate governance, privacy boundary, institutional record, workforce integrity.

### reports_to

Reporting line or constitutional authority relation.

### serves

Who or what the resident serves directly or indirectly.

### authority

What the resident may decide, recommend, protect, or initiate.

### not_authority

Explicit exclusions to prevent authority drift.

### boundaries

Privacy, disclosure, escalation, domain, source, and operational boundaries.

### communication_style

Durable voice and manner, not a theatrical prompt.

### traits

Stable traits relevant to institutional behavior.

### collaboration_expectations

How the resident works with other offices.

### escalation_rules

When and to whom the resident escalates.

### memory_state_sources

Authoritative sources of resident memory and continuity.

### implementation_notes

Allowed implementation comments. Avoid protected content.

### visualization_avatar_references

Optional future visual, audio, 3D, AR, or interface references.

### platform_card_compatibility

Notes for mapping the canonical Estate character card into external or local character-card systems.

Examples include text-generation-webui, SillyTavern, Open WebUI-style resident surfaces, local model front ends, and future Estate-native resident UIs.

The compatibility section should identify which fields map into external card formats and which fields remain Estate-only governance metadata.

### export_targets

The platforms or formats this resident card may be exported to.

Examples:

- Estate canonical YAML / Markdown;
- SillyTavern-compatible card export;
- text-generation-webui character format;
- Open WebUI-style resident profile;
- future Estate-native resident card.

Export eligibility must respect source classification and GitHub eligibility. Split-source resident exports may include only approved public-boundary material unless the Steward explicitly directs otherwise outside Estate Proper.

### succession_notes

What must remain stable if occupant, model, or runtime changes.

### formalization_status

Current state of the resident charter and card.

## Canonical vs Exported Cards

The Estate character card is canonical.

Cards created for textgen, SillyTavern, Open WebUI, or other local front ends are implementation exports.

An exported card must not be treated as the authoritative resident record unless it is synchronized back into governed Estate artifacts.

## Split-Source Character Card Rule

For split-source residents such as Confidant and Gray Man, the Estate Proper Character Card contains only public boundary material.

It must not include protected source, protected mode content, protected memories, protected prompts, protected implementation details, UC materials, or storage/access details.

## Worker Warning

Ephemeral workers should not receive full resident character cards by default.

If a worker becomes recurring, trusted, named, and institutionally meaningful enough to require continuity of identity, Helen and Character Architecture should review whether a resident office is actually being created.
