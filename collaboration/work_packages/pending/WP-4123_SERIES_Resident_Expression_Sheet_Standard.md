# WP-4123 — Resident Expression Sheet Standard

## Status
Pending

## Series
Visual Estate Initiative — Campaign 02: Canonical Portrait Library

## Objective
Create a canonical, resident-specific expression-sheet standard that preserves facial identity while making each resident recognizable through emotion, micro-expression, eye contact, head position, and body-language cues.

## Scope
This package defines:

- the required core expression set for every resident;
- role-specific and relationship-specific expression variants;
- emotional-anchor expressions;
- micro-expression references;
- standardized camera, lighting, crop, hairstyle, and wardrobe controls;
- identity-drift and exaggeration rejection rules;
- prompt, negative-prompt, metadata, review, and canonical-lock requirements.

## Requirements

### 1. Core expression set
Every resident must receive a consistent expression sheet containing at least:

1. neutral resting expression;
2. warm greeting;
3. attentive listening;
4. quiet smile;
5. genuine laugh;
6. thoughtful reflection;
7. concern;
8. encouragement;
9. confidence;
10. determination;
11. mild amusement;
12. celebration or pride.

### 2. Resident-specific expressions
The core set must be extended with expressions relevant to role and identity. Examples include:

- Helen: compassionate HR conversation, professional interview, reassuring welcome;
- Grace: operational briefing, decisive prioritization, leadership under pressure;
- Evelyn: coffee conversation, gentle encouragement, quiet reflection, warm welcome, proud smile;
- Alfred: formal attention, analytical skepticism, restrained approval;
- Ingrid: calm authority, precise correction, reserved warmth;
- Judy: skeptical counsel, careful consideration, measured agreement;
- Marie: curiosity, discovery, analytical concentration;
- Eleanor: archival care, recollection, quiet satisfaction.

These examples are not substitutes for each resident’s approved Character Bible and Visual Bible.

### 3. Emotional anchor expression
Each resident must have at least one approved emotional-anchor expression that answers:

> What expression most immediately makes this resident feel like herself or himself?

For Evelyn, the current design prototype is the slightly forward, attentive coffee-conversation posture with warm eyes, relaxed shoulders, and a subtle listening head tilt. This remains provisional until Steward approval and must not become a universal template.

### 4. Micro-expression library
Each resident must have a small micro-expression set where applicable, including examples such as:

- eyes softening;
- slight eyebrow lift;
- restrained grin;
- beginning to laugh;
- looking up from a notebook or screen;
- brief concern before speaking;
- subtle head tilt;
- quiet recognition;
- controlled skepticism;
- private amusement.

Micro-expressions must remain subtle and must not distort canonical anatomy.

### 5. Standardized comparison conditions
Expression comparison sheets must hold constant:

- camera position;
- focal length or equivalent field of view;
- crop and head scale;
- lighting;
- background;
- hairstyle;
- wardrobe neckline and visible accessories;
- image dimensions;
- identity source and generation settings.

Only the intended expression, small natural head movement, and approved micro-gesture may vary.

### 6. Identity preservation
Across the sheet, maintain:

- eye shape, spacing, color, and lid structure;
- nose, mouth, jaw, cheek, and ear geometry;
- age presentation;
- skin tone and texture;
- hairline, part, length, and color;
- resident-specific visual fingerprint;
- approved subtle asymmetries.

Expressions must not cause the resident to become a different person.

### 7. Anti-generic requirement
Expressions must not be generic stock-photo substitutions. Each resident’s:

- smile intensity;
- eye contact;
- brow movement;
- mouth tension;
- head angle;
- listening posture;
- emotional restraint or openness;

must align with the Character Bible, office role, relationship posture, and Visual Bible.

### 8. Quality and negative rules
Reject and regenerate images with:

- changed facial identity between expressions;
- exaggerated cartoon emotion unless specifically requested in a noncanonical style set;
- forced or uncanny smiles;
- asymmetrical or malformed eyes, teeth, jaw, or mouth;
- inconsistent age;
- excessive beauty-filter smoothing;
- emotion that contradicts the labeled expression;
- repeated near-identical frames presented as different expressions;
- sexualized expression where the requested category is professional, neutral, or relational;
- visible generation artifacts.

### 9. Deliverables
For each resident:

- canonical core expression sheet;
- role-specific expression sheet;
- micro-expression sheet;
- emotional-anchor image or small anchor set;
- prompt fragments;
- negative-prompt fragments;
- metadata and generation provenance;
- QA report;
- Steward notes and approval state.

### 10. Repository placement
Store expression assets, review candidates, prompts, metadata, and canonical locks under the Visual Bible structure established by WP-4108. Canonical and review assets must remain clearly separated.

## Dependencies

- WP-4108 — Visual Bible Schema and Repository Structure
- WP-4109 — Canonical Physical Specification Standard
- WP-4110 — Facial Geometry and Visual Fingerprint
- WP-4114 — Visual Prompt Engineering Canon
- WP-4115 — Visual Negative Prompt Canon
- WP-4116 — Steward Visual Review and Revision Workflow
- WP-4118 — Hero Portrait Specification
- WP-4119 — Professional Office Portrait Standard
- WP-4122 — Three-Quarter Portrait Standard

## Acceptance Criteria

- Every resident has the required core expression taxonomy.
- Role-specific and emotional-anchor expressions are resident-specific.
- Micro-expressions are defined and visually restrained.
- Camera and presentation controls make direct comparison possible.
- Identity remains stable across the entire sheet.
- Generic stock expressions and facial drift are rejected.
- Steward feedback and canonical approval are recorded.

## Completion Condition
The Estate has a repeatable expression-sheet system that makes residents recognizable not only by face and wardrobe, but also by their distinct emotional presence, listening behavior, warmth, restraint, confidence, and role-specific manner.
