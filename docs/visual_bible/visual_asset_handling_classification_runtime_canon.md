# Visual Asset Handling Classification Runtime Canon

Status: Adopted for the visual turntable pipeline branch
Classification: Estate Internal
Authority: Pat / Steward
Date: 2026-07-24

## Purpose

This standard classifies Estate visual assets by content sensitivity and execution-routing requirements. It is intended to prevent sensitive visual assets from being sent to external AI services by accident while preserving the Steward's full authority to view, use, move, approve, or exceptionally route any Estate asset.

This is a handling and routing classification. It is not a restriction on the Steward.

## Governing Distinctions

Three independent fields MUST be recorded where applicable:

1. `handling_class` — what kind of visual material the asset contains.
2. `ai_routing` — where automated processing may occur by default.
3. `steward_authority` — confirms that classification does not limit the Steward's access or decision authority.

A higher handling class does not imply shame, prohibition, or reduced canonical value. It only changes default storage, presentation, collaboration, and AI-routing behavior.

## Handling Classes

### VA-0 — Public / Presentation Safe

Examples:

- approved promotional images;
- public-facing resident portraits;
- presentation graphics;
- wardrobe images intentionally cleared for broad display.

Default AI routing: `external_permitted`

Presentation: unrestricted when otherwise approved.

### VA-1 — Estate Internal

Examples:

- working contact sheets;
- unapproved resident candidates;
- internal diagrams and visual-development artifacts;
- ordinary wardrobe-development images.

Default AI routing: `estate_preferred`

External processing is permitted when operationally useful and consistent with ordinary Estate practice.

### VA-2 — Sensitive Resident Reference

Examples:

- close anatomical or proportion studies;
- undergarment, bodysuit, or minimally clothed technical references;
- identity references that should not appear in ordinary presentations;
- resident visual material requiring deliberate collaboration context.

Default AI routing: `local_preferred`

External processing requires an affirmative operational reason, but no formal exception record is mandatory unless another policy requires it.

### VA-3 — Intimate / Nude Technical Canon

Examples:

- nude resident body canon;
- explicit anatomical turntables created for identity, wardrobe fitting, geometry, or motion consistency;
- derived masks, depth maps, pose references, crops, and transparent outputs that preserve intimate anatomy.

Default AI routing: `local_required`

These assets MUST be processed using Estate-controlled local AI and local tooling by default. External AI processing is allowed only when the Steward specifically decides that a concrete reason justifies it.

A VA-3 external-routing decision SHOULD record:

- who authorized it;
- the specific service or provider;
- the reason local processing was insufficient or unsuitable;
- which assets were sent;
- the date of the decision.

This record is for provenance and deliberate handling, not for restricting the Steward.

### VA-4 — Personally Identifying Intimate Material

Examples:

- intimate visual material depicting a real identifiable person;
- source photography or scans whose disclosure could materially harm a real person;
- intimate assets carrying direct personal identifiers.

Default AI routing: `local_required_strict`

External processing requires explicit Steward authorization and a recorded reason. Additional Ingrid, legal, consent, or privacy review may be required when the material concerns a person other than the Steward.

VA-4 is distinct from a fictional resident's technical body canon. A fictional Evelyn nude canon is normally VA-3, not VA-4.

## AI Routing Values

- `external_permitted` — external or local processing may be used.
- `estate_preferred` — Estate-controlled processing is preferred but not required.
- `local_preferred` — use local AI unless there is a practical reason not to.
- `local_required` — route to local AI by default; external use requires a specific Steward-approved reason.
- `local_required_strict` — route locally; external use also requires a durable authorization record and any applicable privacy or consent review.

## Steward Authority

Every governed manifest using this classification SHOULD include:

```json
"steward_authority": {
  "access_restricted": false,
  "override_authority": "Pat / Steward"
}
```

The meaning is explicit:

- the Steward is not blocked from viewing or operating on the asset;
- local-only routing is a default safety and provenance rule, not a denial mechanism;
- the Steward may authorize a specific exception;
- workers and automation may not silently create that exception themselves.

## Presentation and Collaboration Behavior

- VA-0 may be used in ordinary presentations.
- VA-1 may be shown in Estate-internal collaboration.
- VA-2 should be shown only where technically relevant.
- VA-3 should not be inserted into ordinary decks, broad contact sheets, routine messages, or external collaboration surfaces unless the task specifically requires the intimate technical reference.
- VA-4 should be handled only in the explicitly authorized context.

Derived assets inherit the highest applicable classification unless they no longer expose the sensitive content. Renaming, background removal, resizing, cropping, masking, or format conversion does not automatically lower classification.

## Evelyn Body Canon Classification

Evelyn's proposed nude identity/body turntable is classified:

```json
{
  "handling_class": "VA-3",
  "content_descriptor": "intimate_nude_technical_canon",
  "ai_routing": "local_required",
  "ordinary_presentation": false,
  "steward_authority": {
    "access_restricted": false,
    "override_authority": "Pat / Steward"
  }
}
```

The canon may be used for resident identity consistency, body proportions, wardrobe generation and fitting, motion development, occlusion reasoning, and derived technical maps. Wardrobe-safe outputs may receive a lower classification after deliberate review.

## Required Manifest Fields

A visual asset set governed by this standard SHOULD carry:

```json
"asset_handling": {
  "handling_class": "VA-3",
  "content_descriptor": "intimate_nude_technical_canon",
  "ai_routing": "local_required",
  "ordinary_presentation": false,
  "external_processing": {
    "authorized": false,
    "authorized_by": null,
    "reason": null,
    "provider": null,
    "authorized_at": null
  },
  "steward_authority": {
    "access_restricted": false,
    "override_authority": "Pat / Steward"
  }
}
```

## Worker and Automation Rules

Workers and automated pipelines MUST:

- read the handling classification before selecting an AI provider;
- preserve the classification in derivative manifests;
- default VA-3 and VA-4 assets to local processing;
- avoid placing VA-3 or VA-4 imagery into routine presentation artifacts;
- stop and request or locate Steward authorization before external routing;
- never interpret the classification as restricting the Steward.

Workers MUST NOT:

- silently upload VA-3 or VA-4 assets to an external model;
- lower classification merely because an image is cropped, resized, or background-removed;
- treat nude technical canon as ordinary wardrobe presentation content;
- invent authorization on the Steward's behalf.

## Relationship to Broader Security Governance

This standard is deliberately limited to visual-asset sensitivity and AI-routing behavior. It does not replace Ingrid's broader security authority, personnel permissions, repository classification, consent rules, or future Estate-wide data-classification standards.
