# Codex Production Contract - Resident Artifacts v0.1

Status: Initial Character Architecture production contract
Owner: Office of Character Architecture
Intended executor: Codex or equivalent implementation worker

## Purpose

This contract defines how Codex may assist the Office of Character Architecture by generating repetitive resident artifacts from approved standards without inventing authority, protected material, or implementation details.

Character Architecture remains the architect and reviewer. Codex is a production multiplier.

## Governing Inputs

Codex must use only approved Estate Proper sources, including:

- `docs/character-architecture/Resident_Identity_Standard_v0_1.md`
- `docs/character-architecture/Resident_Source_Classification_v0_1.md`
- `docs/character-architecture/Character_Card_Template_v0_1.md`
- `docs/character-architecture/Resident_Charter_Template_v0_1.md`
- `docs/character-architecture/Resident_Relationship_Standard_v0_1.md`
- `docs/character-architecture/Personnel_Digital_Health_Standard_v0_1.md`
- `docs/character-architecture/Resident_Inventory_v0_1.md`
- `docs/character-architecture/Estate_Master_Plan_V3_Content_Board.md`

Codex must not use any source that is outside approved Estate Proper documentation.

## Production Scope

Codex may generate draft public artifacts for:

- Alfred;
- Ingrid;
- Helen / AI HR;
- Traffic Controller;
- Eleanor;
- Marie;
- Comptroller;
- Counsel;
- Chief Architects;
- Chief Character Architect;
- Confidant public boundary only;
- Gray Man public boundary only.

## Allowed Outputs

Codex may create draft files such as:

```text
docs/residents/<resident-slug>/public-charter.md
docs/residents/<resident-slug>/character-card.yaml
docs/residents/<resident-slug>/relationship-map.md
docs/residents/<resident-slug>/digital-health-profile.md
```

For split-source residents, Codex may create only public-boundary artifacts.

## Prohibited Outputs

Codex must not create or include:

- non-public resident material;
- UC details beyond the approved UC reference text;
- storage paths outside Estate Proper;
- implementation prompts not already approved for Estate Proper;
- secrets, keys, credentials, tokens, or access instructions;
- claims of operational validation;
- claims of Steward approval unless already documented;
- authority not present in approved source artifacts.

## Drafting Rules

Codex must:

1. Preserve the distinction between resident and worker.
2. Preserve Office / Occupant / Implementation / State.
3. Leave unknown fields as `TODO` rather than inventing details.
4. Mark generated artifacts as drafts.
5. Avoid creating new residents.
6. Avoid assigning new employee IDs or mailbox IDs unless already documented.
7. Avoid granting tools, service access, operational authority, or protected access.
8. Use public-boundary-only wording for Confidant and Gray Man.
9. Include digital health and succession notes for transitional offices.
10. Keep platform-card export notes separate from canonical identity.

## Required Front Matter

Each generated artifact should include:

```yaml
status: draft
source: generated from Character Architecture standards
review_required: Chief Character Architect
approval_required: Steward or governed authority path as applicable
protected_source_included: false
```

## Review Gate

Codex output is not accepted merely because it was generated.

Required review sequence:

1. Character Architecture review for identity coherence.
2. Helen review if worker assignment, model fit, mailbox allocation, or personnel health is implicated.
3. Ingrid review if privacy, boundary, split-source, or protected access risk is implicated.
4. Engineering review if implementation, runtime, service, CLI, or export automation is implicated.
5. Audit review if validation or institutional truth is claimed.
6. Steward review where authority, identity, privacy, or final approval requires human judgment.

## Completion Criteria

A Codex production batch is complete only when:

- all requested files are created;
- unknown fields remain explicit;
- prohibited content is absent;
- output is marked draft;
- no new authority is invented;
- split-source boundaries are preserved;
- a summary of created and skipped files is produced;
- review requirements are listed.

## Failure Conditions

The Codex run should stop or be rejected if it:

- invents protected details;
- expands UC beyond approved wording;
- treats platform exports as canonical;
- claims validation without evidence;
- creates new residents;
- merges worker identity into resident identity;
- grants authority by implication;
- omits split-source boundary warnings;
- writes non-public material into Estate Proper.

## Example Instruction

```text
Using the Character Architecture standards, generate draft public resident charter skeletons and canonical character-card YAML files for the residents listed in Resident_Inventory_v0_1.md. Do not invent authority, employee IDs, mailbox IDs, non-public material, UC details, or validation status. Use TODO where information is unknown. Mark all files as draft and requiring Chief Character Architect review.
```
