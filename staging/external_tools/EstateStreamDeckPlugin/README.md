# Temporary External Tool Staging

This directory is a temporary transport channel for tools that are not part of the Estate runtime architecture.

## Rules

- Files here may be synchronized through the Estate repository for delivery.
- After synchronization, copy the tool to its authoritative external location before execution.
- Do not import this directory into Estate runtime code.
- Do not treat these tools as Estate-owned components.
- Remove completed transfer artifacts when they are no longer needed.

## Current delivery

`Install-Estate-LongPress-ComfyUI.ps1`

Authoritative destination after sync:

`A:\AI\Tools\EstateStreamDeckPlugin\scripts\Install-Estate-LongPress-ComfyUI.ps1`
