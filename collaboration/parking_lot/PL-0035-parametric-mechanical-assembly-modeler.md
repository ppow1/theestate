# PL-0035 — Parametric Mechanical Assembly Modeler

Status: Captured
Priority: Strategic
Category: Mechanical Design / Parametric Modeling / AI-Assisted Engineering
Originator: Pat / Steward
Date Captured: 2026-08-01
Target Milestone: After current Engineering capability and local coding-model evaluation are stable

## Idea

Design a local, scriptable parametric mechanical assembly system that restores and modernizes the Steward's earlier data-driven CAD workflow.

The system should allow a complete assembly to be described in a spreadsheet, JSON, or equivalent machine-readable model using primitives, imported meshes, named reference points and planes, parent-child relationships, relative and absolute transforms, stack-up relationships, tolerances, clearances, and change dependencies.

The authoritative assembly model should be usable with or without a conventional CAD application. CAD generation is one output of the model, not the only place where the design exists.

The intended operating pattern is:

```text
Spreadsheet / JSON assembly definition
  -> dependency and transform resolver
  -> collision / proximity engine
  -> interactive 3D visualization
  -> change-impact and constraint report
  -> optional CadQuery / FreeCAD / STEP / STL output
```

## Core Capabilities

- Primitive geometry such as boxes, cylinders, planes, pockets, envelopes, and simplified components.
- Imported STL, STEP, or other geometry where appropriate.
- Hierarchical assemblies with parent-child transforms.
- Named anchors, reference points, axes, and planes.
- Absolute and relative placement.
- Stack-up dimensions and calculated relationships.
- Tolerance, clearance, minimum-wall, and fit rules.
- Dependency propagation when a dimension, parent, or reference changes.
- Static collision detection.
- Minimum-distance and proximity reporting.
- Contact points, penetration depth, contact normals, and approach direction where supported.
- Swept-path or insertion-path collision checks for serviceable/removable assemblies.
- Interactive visualization with transparency, collision highlighting, contact arrows, and selectable parts.
- Change-impact reporting showing what moved, what failed, what remained valid, and what requires review.
- Scripted generation of revised pockets, mounts, brackets, bosses, and printable geometry.
- STEP, STL, 3MF, DXF, section-view, and report outputs where supported.
- Versionable, readable source definitions suitable for Git-based review.
- Natural-language assistance for changing parameters, proposing relationships, generating scripts, and interpreting results.

## Initial Demonstration Use Case

Use the Halo-bot 3D printed assembly as the first bounded demonstration.

The immediate problem is to place a magnetic pogo connector and removable electronics cassette inside the lower body while preserving practical wire space, assembly access, serviceability, shell clearance, and printable structure.

The first demonstration should support:

- the three existing STL files;
- a simplified or imported pogo connector;
- the removable electronics cassette;
- magnet pockets and mating references;
- a practical wire-volume envelope;
- bottom mating/contact plane;
- connector orientation and placement search;
- collision and clearance visualization;
- insertion/removal path checking;
- candidate comparison;
- placement transform and optional modified-print geometry output.

Wire bend radius is a practical consideration but should not dominate the design. The key requirement is sufficient stable wire space without severe bends, because the pogo connection removes repeated cable movement from the service interface.

## Proposed Technical Direction

Investigate a practical local stack built from established open-source components, potentially including:

- Python as the scripting and orchestration language;
- a canonical JSON assembly model with optional spreadsheet import/export;
- trimesh, Open3D, PyVista, FCL bindings, or equivalent for mesh handling, transforms, proximity, and collision analysis;
- a local Three.js or equivalent WebGL viewer for interactive visualization;
- CadQuery / OpenCascade for scriptable solid generation and export;
- FreeCAD for optional interactive CAD inspection, TechDraw, and manual refinement;
- a local coding model for implementation assistance;
- a local vision-language model for reviewing rendered candidates, not for replacing geometry calculations.

The geometry and collision engines must remain authoritative for physical facts. AI may translate intent, generate code, propose relationships, rank measured candidates, and explain reports, but it must not be treated as the source of truth for collision, clearance, fit, or dimensional validity.

## Why It Is Parked

The idea is strategically valuable and likely feasible with current open-source tools and local AI assistance, but it should not interrupt the current Estate capability campaign.

Before promotion, the Estate should finish the active Help/Skills closeout, complete the local coding-model selection or establish another qualified engineering worker, and gather the actual Halo-bot source files and component dimensions needed for a bounded prototype.

This capture preserves the product architecture and the Steward's prior design experience without authorizing implementation.

## Promotion Condition

Promote this idea when:

1. The Steward intentionally selects it as an active mechanical-design capability or product project.
2. The three Halo-bot STL files and pogo/cassette dimensions are available in an approved workspace.
3. A qualified coding worker is available for a bounded implementation campaign.
4. The initial scope is limited to a vertical slice: assembly definition, transforms, collision/proximity, visualization, impact reporting, and one export path.
5. The Estate determines whether the result belongs as an Estate capability, a standalone local tool, or both.

## Explicit Non-Action

Do not begin implementation, install CAD/collision packages, modify the Halo-bot models, create a new Estate department, or treat this capture as authority to execute.

Do not assume a language model alone can solve spatial fit from screenshots or text. Exact geometry must be measured and validated programmatically.

## Related Evidence

- Steward's historical AutoCAD scripting and spreadsheet-driven electronics-packaging workflow.
- Steward's historical use of game-development collision detection around primitive objects for standalone visualization and contact-angle reasoning.
- Current Halo-bot pogo connector and removable electronics cassette packaging problem.
- Current discussion of CadQuery, FreeCAD, Python geometry search, scene graphs, collision detection, and local vision-language review.
- Canonical Parking Lot process: `AI_COMMUNICATION_HINTS.md`.
