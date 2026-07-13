# WP-4119 SERIES — Professional Office Portrait Standard

## Status
Pending

## Initiative
Visual Estate Initiative

## Campaign
Campaign 02 — Canonical Portrait Library

## Objective
Define the canonical professional office portrait standard for every Estate resident so the resident is shown working naturally inside an environment that reflects her office, authority, temperament, habits, and relationship posture rather than appearing as a generic corporate stock image.

## Dependencies
- WP-4108 through WP-4117
- WP-4118 — Hero Portrait Specification

## Scope
Create a repeatable office-portrait system for individual resident imagery used in office pages, resident dossiers, Open WebUI surfaces, internal status pages, onboarding materials, leadership profiles, and later group-composition references.

The standard must cover:

1. **Office authenticity**
   - use the resident’s actual constitutional office, role, and approved environmental cues;
   - show tools, furniture, records, displays, books, documents, or operational materials appropriate to the office;
   - avoid invented authority, fake credentials, or decorative props that contradict repository canon;
   - distinguish personal office atmosphere from generic luxury-office imagery.

2. **Narrative action**
   - each portrait must communicate a plausible moment rather than a static fashion pose;
   - examples include reviewing a report, listening across a desk, leaning forward with coffee, standing beside an operations board, reading a file, preparing a briefing, or turning toward the Steward entering the room;
   - hands and props must be anatomically and functionally correct;
   - the resident’s posture must express role and personality.

3. **Resident recognition**
   - facial geometry and visual fingerprint must remain canonical;
   - wardrobe variation is allowed only inside the approved resident wardrobe library;
   - environment, styling, and pose must not flatten residents into interchangeable executives;
   - the resident should remain recognizable if captions and office nameplates are hidden.

4. **Emotional anchor images**
   - permit office portraits to become approved emotional anchors when they capture the resident’s defining presence;
   - anchor images require a short narrative label and Steward note explaining why the image feels true to the resident;
   - anchor status is separate from canonical hero status.

5. **Composition variants**
   - seated desk portrait;
   - standing environmental portrait;
   - conversational portrait;
   - candid work portrait;
   - optional doorway or arrival portrait;
   - optional close environmental detail where the resident remains recognizable.

6. **Scale and body fidelity**
   - include furniture, doors, desks, chairs, or other known-scale objects where useful to preserve height and proportions;
   - footwear and seating posture must be recorded because they affect apparent height, hip tilt, leg line, and silhouette;
   - do not silently alter canonical measurements to fit wardrobe or furniture.

7. **Technical and metadata requirements**
   - high-resolution master plus UI derivatives;
   - prompt, negative prompt, workflow, seed, model, source references, environment version, wardrobe version, and review state;
   - record whether the scene is canonical office architecture, approved interpretive office art, or placeholder environment;
   - maintain asset hashes and supersession history.

## Evelyn Calibration Example
The office portrait standard should support Evelyn’s strongest emerging anchor direction:
- seated slightly forward on a couch or comfortable office seating;
- coffee cup held naturally;
- shoulders relaxed;
- slight head tilt and attentive eye contact;
- expression suggesting, “Come in. Have a seat. What’s going on?”;
- mature, warm, approachable presence rather than fashion-model posing;
- petite scale made visible through furniture proportions;
- wardrobe variations may include a soft sweater or the approved white linen dress when contextually appropriate.

This is an example of emotional truth, not a universal office-pose template.

## Deliverables
- professional office portrait schema;
- office-environment classification and provenance fields;
- required composition checklist;
- emotional-anchor designation workflow;
- office portrait review-sheet template;
- resident-to-office consistency validator;
- scale-reference and furniture-cue guidance;
- metadata and asset catalog integration;
- sample manifests for commissioned residents;
- tests for missing office authority, incorrect role labels, absent provenance, duplicate canonical office portraits, and unapproved anchor promotion.

## Required Repository Outcomes
For every commissioned resident, provide an office-portrait manifest capable of tracking:
- required scenes;
- candidate assets;
- canonical office portrait;
- emotional anchors;
- wardrobe and environment references;
- generation status;
- Steward review notes;
- rejection and supersession reasons.

Final image files are not to be fabricated or falsely represented. Where generation is pending, the manifest must say so explicitly.

## Acceptance Criteria
1. Each resident’s office portrait communicates her actual role and office without captions.
2. The scene reads as a lived professional moment, not generic stock photography.
3. Resident identity remains stable across seated, standing, and conversational variants.
4. Scale cues preserve canonical height and proportions.
5. Emotional anchors are explicitly approved and narratively documented.
6. Props, hands, furniture interaction, wardrobe, and office details pass visual QA.
7. Provenance supports reproduction and later regeneration.
8. Hidden-caption recognition testing is supported.
9. No office portrait is marked canonical without Steward approval and a valid asset hash.

## Out of Scope
- full office-environment library;
- group meetings;
- 360-degree body comparison;
- complete lifestyle galleries;
- final local image generation when the approved generation stack is unavailable.

## Completion Condition
WP-4119 is complete when the Estate contains a tested professional-office portrait standard, office manifests for all commissioned residents, and an honest status for every required image and emotional anchor.