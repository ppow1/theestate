# WP-0648 - Power-Loss-Safe Windows Runtime Lock Recovery

Status: Proposed  
Priority: Critical  
Owner: Chief Architect  
Classification: Estate Internal  
Created: 2026-07-11

## Mission

Repair the Estate Operations Runtime host so that an unclean Windows shutdown or power loss cannot leave automatic validation permanently blocked by an indeterminate stale lock owner.

The live failure observed after a power outage is:

```text
Operations runtime blocked: operations runtime lock owner liveness uncertain for pid 4720
```

The runtime must preserve duplicate-host