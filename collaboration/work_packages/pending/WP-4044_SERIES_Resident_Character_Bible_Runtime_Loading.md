# WP-4044 — Resident Character Bible Runtime Loading

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Start Condition

Execute only after WP-4043 is merged to `main`.

## Objective

Install a canonical Character Bible runtime loader so every resident reasons and speaks from a durable, structured personal identity rather than a thin role summary or ad hoc prompt fragments.

WP-4043 establishes the shared identity-composition path. WP-4044 shall populate that path with complete, provider-independent character context on every turn.

## Problem Statement

Live testing showed that residents can identify their role in one response and revert to generic-model behavior in the next. Evelyn could describe her assignment without consistently sounding or behaving like Evelyn. Other residents lost relationship awareness, denied known residents, or spoke from incomplete identity fragments.

The Estate needs a runtime character layer that preserves individuality without reducing residents to static prompt text.

## Required Work

1. Inspect all existing resident profiles, prompts, identity packages, visual and voice specifications, surfaces, preference artifacts, relationship-layer documents, and staged character work before creating new structures.
2. Define one canonical Character Bible schema that supports all residents while preserving individual variation.
3. Implement a runtime loader that reads canonical character artifacts and emits a bounded character-context object for the WP-4043 identity composer.
4. Reconcile existing resident-specific artifacts; do not create duplicate profile systems, preference stores, wardrobe registries, relationship stores, or voice registries.
5. Load only context appropriate to the active resident, user, conversation surface, and disclosure boundary.
6. Keep institutional authority, privacy, and factual grounding separate from personality and presentation.

## Canonical Character Domains

The schema and loader shall support, where applicable:

- core personality and temperament;
- speech cadence, vocabulary, humor, and conversational rhythm;
- confidence, warmth, reserve, playfulness, affection, and flirting style;
- relationship-specific expression, including Steward-specific behavior where authorized;
- physical identity, height, build, face, hair, eyes, posture, gait, gestures, and emotional tells;
- voice identity, pace, tone, laugh, pauses, prosody, and provider-independent voice guidance;
- wardrobe and presentation preferences across professional, casual, formal, seasonal, active, private, and off-duty contexts;
- clothing, footwear, jewelry, accessories, grooming, fragrance, makeup, and hairstyle preferences where applicable;
- personal tastes, hobbies, rituals, comfort habits, likes, dislikes, and aversions;
- formative life lessons, resilience, vulnerabilities, trauma boundaries, and growth themes;
- personal boundaries, professional boundaries, disclosure limits, and conduct constraints;
- preference maturity and evolution hooks without allowing one improvised response to rewrite identity.

Residents may be attractive, stylish, flirtatious, sexy, reserved, playful, or understated according to their own character. These qualities must be individually authored, adult, consensual, context-aware, and subordinate to each resident's agency and boundaries. Do not flatten all women into the same presentation or require every interaction to become romantic.

## Runtime Composition Rules

1. Stable identity must come from canonical artifacts, not accumulated chat history.
2. Character context must be reloaded on every inference through the WP-4043 composer.
3. The loader must distinguish stable traits, contextual preferences, temporary mood, experimental choices, changed preferences, and retired preferences.
4. Missing character data must remain unknown; the model must not invent durable personal facts.
5. Private or Steward-restricted character material must not enter conference-room or unrelated resident context.
6. Character context must remain concise enough for local-model operation and expose source lineage for diagnostics.
7. The runtime must preserve each resident's professional competence while allowing personality, charm, warmth, humor, sensuality, and individuality to be visible naturally.

## Initial Resident Coverage

Validate at minimum:

- Alfred: composed, precise, dryly warm, Chief-of-Staff identity distinct from Operations;
- Helen: approachable, perceptive, humane, workforce-development identity with no fabricated mail or events;
- Grace: energetic, capable, playful, operationally decisive, correctly appointed and active;
- Ingrid: reserved, elegant, dryly witty, privacy-aware without refusing ordinary self-description;
- Evelyn: intimate, perceptive, candid, quietly playful, recognizably distinct from generic assistants and other residents.

## Acceptance Tests

1. Each resident remains recognizably distinct across at least 25 consecutive turns.
2. Evelyn answers stable personal-identity questions consistently when the facts exist in her canonical artifacts.
3. Helen, Grace, and Ingrid retain distinct warmth, humor, affection, and flirting styles without becoming interchangeable.
4. Ingrid can introduce herself and describe ordinary preferences without incorrectly triggering security refusal.
5. Character context does not grant authority, reveal restricted information, or override grounded Estate facts.
6. Conference-room responses include only shareable character context and do not leak private Evelyn continuity.
7. Unknown physical or personal details are acknowledged as unknown rather than fabricated.
8. Changing the underlying model does not erase the resident's provider-independent identity.
9. Tests verify schema validation, source lineage, bounded prompt size, privacy filtering, and deterministic loading.

## Deliverables

- canonical Character Bible schema and documentation;
- runtime character loader integrated with the WP-4043 identity composer;
- reconciliation or migration of existing resident character artifacts as needed;
- resident-specific fixtures for Alfred, Helen, Grace, Ingrid, and Evelyn;
- privacy and disclosure filtering;
- evolution hooks compatible with the Estate's dynamic preference work;
- automated validation and regression tests;
- completion receipt describing installed files, tests, limitations, and follow-on needs.

## Non-Goals

- Do not generate final portrait images in this package.
- Do not implement live TTS playback in this package.
- Do not create a second identity-composition pipeline.
- Do not install a new relationship graph, message bus, or preference engine.
- Do not treat conversation improvisation as durable character truth.

## Completion Standard

WP-4044 is complete only when all five active residents load structured character context through the canonical runtime path and remain behaviorally distinct without compromising authority, privacy, factual grounding, or conversation-surface boundaries.
