# WP-0647 - Estate Feature Activation and Orphaned Capacity Integration

Status: Proposed  
Priority: Critical - First Priority  
Owner: Chief Architect  
Classification: Estate Internal  
Created: 2026-07-11

## Mission

Bring merged and validated Estate capabilities into truthful operational use before continuing the autonomous Ring 2 roadmap.

The Estate currently contains capabilities that fall into different states:

1. implemented and live,
2. installed into active source paths but not connected to their intended callers,
3. staged and validated but not installed,
4. planning-only,
5. blocked or incomplete.

This package must establish one authoritative activation ledger, prove the real runtime reachability of each implemented capability, and safely connect every eligible orphaned capability to the existing Estate surfaces that should use it.

This is an activation and integration package. It must not create a second registry, scheduler, queue, authority system, Office, resident gateway, model-control plane, or validation engine.

## First-Priority Rule
