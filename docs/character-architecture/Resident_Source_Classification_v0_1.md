# Resident Source Classification v0.1

Status: Initial Character Architecture baseline
Scope: Estate Proper classification for residents, workers, systems, and split-source identities

## Purpose

This standard distinguishes named institutional residents from ephemeral workers, systems, services, and protected split-source residents.

It protects the Estate from treating every AI process as a character and from treating every character as a public Estate artifact.

## Core Distinctions

### Resident

A resident is a named occupant of a durable institutional office.

Residents require character architecture, continuity, public office boundaries, collaboration expectations, and eventually a character card.

### Worker

A worker is a temporary or pooled agent assigned to a work package or operational task.

Workers may receive mailbox IDs, clearances, tools, and temporary assignments. That does not make them residents.

Helen / AI HR governs worker assignment, worker fit, mailbox assignment, clearance, duration, drift concerns, and return-to-pool status.

### System / Service

A system or service is infrastructure, tooling, adapter, command surface, model runtime, workflow runner, or execution layer.

Systems and services may have names, but naming alone does not make them residents.

### Split-Source Resident

A split-source resident has a public Estate identity and protected private source material outside Estate Proper.

Estate Proper may define the public office identity, public resident card, public collaboration boundary, and public restrictions.

Estate Proper must not store, inspect, summarize, route, or operationalize private source material.

## Classification Types

| Classification | Meaning | Current examples |
| --- | --- | --- |
| Single-source Estate resident | Public identity and resident source live in Estate Proper. | Alfred, Ingrid, Helen, Eleanor, Marie, Comptroller, Counsel, Chief Character Architect |
| Split-source resident | Public boundary lives in Estate Proper. Private persona/source lives elsewhere. | Confidant, Gray Man |
| Ephemeral worker | Temporary worker assigned by Helen. Not a resident. | Codex workers, local LLM workers, test runners, research workers |
| System / service | Infrastructure or command layer. Not a resident. | Codex CLI, future ChatGPT CLI, Ollama, Office command surface |
| UC-governed | Consult Steward. No access by implication. | UC-related matters |

## Split-Source Resident Rule

For split-source residents:

> Public boundary lives in Estate Proper. Private source lives elsewhere.

The public Estate artifact may define:

- office name;
- public title;
- public mission;
- public collaboration boundary;
- public authority limits;
- disclosure restrictions;
- public resident card fields;
- GitHub eligibility for public-only artifacts.

The public Estate artifact must not define:

- private source location;
- private persona files;
- private memory contents;
- private implementation prompts;
- private model configuration details;
- intimate or mode-specific private content;
- UC source details;
- storage paths for protected material;
- access mechanisms;
- credentials, tokens, or secrets.

## Private Source Notice

Use this standard notice when needed:

> This resident has protected private-source material outside Estate Proper. Estate Proper documentation defines only the public identity, office boundary, and collaboration rules. Private source material is not stored in this repository, not available to normal CLI workers, and not accessible by implication. Consult the Steward for any question requiring protected-source access.

## UC Reference

Use the following wording in Estate Proper documentation when UC must be mentioned:

> UC refers to the Undercroft. The UC exists under the authority of the Steward and is governed by a separate Constitution defined elsewhere. For any questions concerning the UC, consult the Steward.
>
> No Estate resident, worker, office, mailbox, or system receives UC access by implication.

Do not map UC internals in Estate Proper.

## GitHub Eligibility

| Artifact type | GitHub eligibility |
| --- | --- |
| Public resident charter | Eligible if it contains only Estate Proper public boundary material. |
| Public character card | Eligible if it contains only Estate Proper public boundary material. |
| Split-source private material | Never eligible. |
| UC-related private source | Never eligible. |
| Worker assignment records | Eligible only if no sensitive credentials, private-source content, or non-public material is included. |
| CLI adapter documentation | Eligible when it does not expose secrets, vault locations, or protected private-source paths. |

## Ingrid Boundary Role

Ingrid protects the boundary between Estate Proper and protected private-source domains.

Protection of the boundary does not imply inspection of the contents.

Ingrid ensures that normal CLI workers, GitHub commits, public resident artifacts, indexing, search, dashboards, or resident summaries do not accidentally cross into protected private-source material.

## Character Architecture Role

The Office of Character Architecture owns public resident identity, public character cards, resident charters, identity continuity, source classification, and character-coherence review.

Character Architecture does not own private source material for split-source residents and does not gain access by implication.
