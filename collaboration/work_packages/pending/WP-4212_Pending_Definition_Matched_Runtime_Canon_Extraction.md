# WP-4212 — Pending-Definition-Matched Runtime-Canon Extraction

## Status

Pending

## Summary

Implement conversation extraction around detected work-package outputs rather than reconstructed conversational assignment scope.

The engine must scan archived conversations for assistant-produced runtime-canon or supporting-design blocks, resolve each apparent work-package identifier against the authoritative files under `collaboration/work_packages/pending/`, load the matching pending definition, evaluate whether the conversational output is a complete or usable supporting response to that definition, and preserve qualifying material