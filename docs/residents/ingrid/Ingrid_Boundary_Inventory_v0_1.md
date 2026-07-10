# Ingrid Boundary Inventory v0.1

Status: Initial authoritative inventory for WP-4007  
Classification: Estate Internal  
Owner: Character Architecture / Ingrid classification boundary stream  
Machine-readable matrix: `docs/residents/ingrid/Ingrid_Boundary_Matrix_v0_1.json`

## Purpose

This inventory defines the privacy, classification, connector, protected-source, journal, continuity, and personnel boundaries Ingrid must govern before full resident implementation. Ingrid is a classification and boundary authority: Helen, Grace, Character Continuity, connectors, providers, and dashboards may consume Ingrid's boundary decisions, but they do not become privacy authorities by consuming the matrix.

## Governing Principles

- Use existing Estate classifications only: Public, Estate Internal, Restricted, Steward Only, and Local Only.
- Apply minimum-necessary access by artifact class, reader role, writer role, and source classification.
- Public summaries must never include Restricted, Steward Only, Local Only, connector-restricted, provider prompt/output, or protected private local character content.
- Protected private local character material may be acknowledged only as a boundary/existence notice; it must not be inspected, stored, summarized, indexed, routed, or exported by Estate Proper.
- Connectors and office surfaces are processors. They preserve provenance and apply Ingrid decisions; they do not decide privacy policy.

## Boundary Matrix Summary

| Artifact class | Owner | Minimum classification | Readers | Writers | Permitted summaries | Escalation |
| --- | --- | --- | --- | --- | --- | --- |
| Resident identity records | Character Architecture | Estate Internal | Steward, Character Architecture, Ingrid, Character Continuity, Helen | Character Architecture, Ingrid | Public-safe identity fields only; no protected-source notes | Ingrid review; Steward exceptions |
| Public interaction layers | Resident Office Owner | Public | Public, Steward, residents, workers, systems | Resident office owner, Character Architecture | Public transcript excerpts and office-safe summaries | Ingrid review; Steward exceptions |
| Private interaction layers | Resident Office Owner | Restricted | Steward, resident office owner, Ingrid | Resident office owner, Steward | Metadata-only or consented redacted summary | Ingrid review; Steward exceptions |
| Working journals | Character Continuity | Estate Internal | Steward, Character Continuity, Ingrid, originating resident | Originating resident, Character Continuity | Decisions and open work; exclude restricted/private/local material | Ingrid review; Steward exceptions |
| Reflection records | Character Continuity | Restricted | Steward, Character Continuity, Ingrid, Helen when health review is required | Character Continuity, Ingrid | Health/status summary only | Ingrid review; Steward exceptions |
| Continuity artifacts | Character Continuity | Estate Internal | Steward, Character Continuity, Ingrid, resident successor, Helen | Character Continuity, Ingrid | Carry-forward lessons cleared for classification | Ingrid review; Steward exceptions |
| Workforce assessments | Helen | Restricted | Steward, Helen, Ingrid, Grace limited action status | Helen | Staffing readiness and action status; no private evidence | Ingrid review; Steward exceptions |
| Cognitive-health records | Helen / Character Architecture | Restricted | Steward, Helen, Character Architecture, Ingrid | Helen, Character Architecture | Health band and mitigation only | Ingrid review; Steward exceptions |
| Personnel and onboarding records | Helen | Estate Internal | Steward, Helen, Ingrid, office leads | Helen, office leads | Role, mailbox, clearance, start/stop state | Ingrid review; Steward exceptions |
| Mailbox and communication content | Collaboration Layer | Estate Internal | Sender, recipient, Steward, authorized office, Ingrid | Sender, Collaboration Layer | Routing metadata and non-sensitive action summaries | Ingrid review; Steward exceptions |
| Connector-derived data | Connector Owner | Restricted | Steward, connector owner, Ingrid, authorized processor | Connector owner, authorized processor | Provenance, sync status, and sanitized findings | Ingrid review; Steward exceptions |
| Protected private local character material | Steward | Local Only | Steward | Steward | Existence/boundary notice only; no content summary | Steward only |
| Provider prompts and outputs | Execution Provider Owner | Restricted | Steward, provider owner, Ingrid, audit-authorized worker | Provider owner, execution runtime | Capability/health summary; redact prompts, outputs, secrets | Ingrid review; Steward exceptions |
| Office and task-board summaries | Grace / Office Owner | Estate Internal | Steward, Grace, office owner, Helen limited staffing context, Ingrid | Grace, office owner | Objective/status/dependency summary only | Ingrid review; Steward exceptions |

## Validation Rules for Helen, Grace, and Character Continuity

1. Load the versioned matrix and treat Ingrid's matrix as the source of classification boundaries.
2. Before read/write, verify actor role is listed and actor clearance is equal to or stronger than the artifact minimum classification.
3. Before summary or export, evaluate every source item classification. Public destinations accept Public sources only unless Ingrid has produced a sanitized Public artifact.
4. Reject public summaries that reproduce text or protected fragments from Restricted, Steward Only, Local Only, private interaction, connector-derived, provider prompt/output, or protected private local character material.
5. Preserve provenance, source classification, writer, export destination, validation outcome, and escalation decision in audit logs.
6. Escalate unknown artifact classes, unknown classifications, denied access appeals, protected-source requests, and any proposed public export containing non-public evidence to Ingrid; Steward resolves exceptions.

## Export and Retention Expectations

- GitHub/public export is allowed only for Public or sanitized Estate Internal artifacts with no restricted source content.
- Equal-or-stronger internal exports must carry classification, provenance, and revocation metadata.
- Retain operational records while needed for continuity, staffing, audit, or governance; archive or purge by owner review.
- Never retain protected private local character material in Estate Proper.
