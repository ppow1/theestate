# PL-0038 — Estate Deal Discovery and Hardware Acquisition Assistant

Status: Captured  
Category: Procurement / Market Intelligence / AI-Assisted Acquisition  
Priority: High  
Originator: Pat / Steward  
Date captured: 2026-08-06  
Target milestone: After current Comms8 integration and operational stabilization

## Idea

Create a read-only Estate assistant that discovers selected hardware and equipment listings from intentionally approved marketplace sources, normalizes and deduplicates them, and identifies the small number that may deserve Steward review. Initial interests include AI infrastructure servers, GPU cards and systems, workstation/server components, storage, networking, accelerators, and unusual local or online equipment opportunities.

The capability should distinguish genuinely interesting opportunities from ordinary keyword matches by considering requested specifications, total acquisition cost, condition, seller and listing risk indicators, missing components, upgrade or repair cost, likely Estate usefulness, duplicates, listing age, urgency, confidence, and transparent recommendation reasons.

This item grants no purchase authority.

## Why It Is Parked

The Estate has not yet selected one bounded source and item profile, documented the source's supported access path and restrictions, or approved a read-only implementation package. Current Comms8 integration and operational stabilization remain higher priority.

## Existing Subsystem Fit

Prefer extending the existing Assets/Acquisitions responsibility represented by `operations/assets/acquisitions/`, with Discovery used for collection and analysis where appropriate. Do not create a new department, broad procurement platform, registry, or scheduler unless the bounded investigation proves existing systems cannot absorb the work.

## Promotion Condition

The Steward intentionally selects a bounded marketplace and item profile; a supported or explicitly authorized read-only acquisition method is identified; marketplace access constraints are documented; and the first implementation can be limited to collection, normalization, scoring, deduplication, and notification without messaging sellers or purchasing.

## Explicit Non-Action

Do not scrape marketplaces, access private accounts, bypass login controls, defeat anti-bot systems, evade rate limits, create marketplace accounts, contact sellers, bid, negotiate, make offers, purchase, store credentials or session cookies, or deploy persistent monitoring merely because the idea has been captured.

## Current Steward Direction

The Steward's 2026-08-06 instruction intentionally promotes this item only into a bounded architecture and feasibility investigation. It does not promote implementation or operational monitoring.

## Related Evidence

- `operations/assets/acquisitions/2026-07-31-nvidia-tesla-p100-16gb.md`
- `docs/operations/PL-0038-deal-discovery-bounded-investigation.md`
