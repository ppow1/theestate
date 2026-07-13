# WP-4128 — 360° Capture Standard

**Series:** Visual Estate Initiative — Campaign 03

**Status:** Pending

## Objective

Define the canonical 360° resident capture standard used to evaluate body proportions, posture, silhouette, wardrobe behavior, and identity consistency from all required angles.

## Scope

This package establishes the minimum resident turnaround set:

- front
- front-left 45°
- left profile
- rear-left 45°
- rear
- rear-right 45°
- right profile
- front-right 45°

Optional intermediate angles may be added when a resident's silhouette or wardrobe requires finer inspection.

## Capture Controls

Every angle in a set must preserve:

- the same resident identity reference
- the same canonical or review measurement variant
- the same camera height
- the same focal length
- the same camera distance
- the same lighting rig
- the same background
- the same wardrobe
- the same footwear
- the same neutral facial expression
- the same normalized posture

## Required Deliverables

1. A documented eight-angle capture template.
2. A machine-readable angle manifest.
3. Standard filename rules.
4. Canonical and review asset directories.
5. Generation metadata for each image.
6. A validation checklist confirming cross-angle identity stability.

## Asset Naming

Use deterministic names containing:

- resident identifier
- variant identifier
- angle identifier
- footwear identifier
- wardrobe identifier
- review or canonical state
- revision number

## Quality Requirements

The set fails when:

- the face changes materially between angles
- body proportions drift between views
- height or limb length changes
- clothing changes cut, length, or fit
- footwear changes unexpectedly
- the background or camera geometry changes enough to interfere with comparison
- any angle hides the silhouette being evaluated

## Governance

Turnarounds are review assets until explicitly accepted by the Steward. No measurement choice becomes canonical merely because a complete turnaround exists.

## Dependencies

- WP-4108
- WP-4109
- WP-4110
- WP-4111
- WP-4112
- WP-4114
- WP-4115
- WP-4116

## Acceptance Criteria

- The complete angle set is defined.
- Camera and presentation controls are explicit.
- The standard supports both flat footwear and heel-based comparison sets.
- The output can be consumed by later vertical comparison and canonical-lock workflows.
- The Steward can identify cross-angle inconsistencies without reconstructing generation settings manually.
