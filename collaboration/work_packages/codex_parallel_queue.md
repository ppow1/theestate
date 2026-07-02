# Codex Parallel Launch Queue

## Queue Status

- Status: ready for Steward review; no out-of-series Codex launch items are currently available.
- Scope: pending work packages without completion records that are safe to launch outside the active SERIES queue.
- Current ready parallel queue length: 0 work packages.
- Last refreshed: 2026-07-02.

## Launch Items

No pending work packages are currently safe to launch in parallel outside the active SERIES queue.

## Dependency Notes

- Completed packages are excluded when a matching completion record exists in `collaboration/work_packages/completions/`.
- The remaining pending packages without completion records are `WP-0043`, `WP-0044`, and `WP-0045`.
- `WP-0043` is the next active SERIES implementation package and should remain in the series queue rather than this parallel queue.
- `WP-0044` creates the Resident Card framework for the Office of the Steward and should wait for the Steward Command Center skeleton from `WP-0043`.
- `WP-0045` adds a Steward Decision Queue panel to the Office of the Steward and should wait for the Steward Command Center skeleton from `WP-0043`.

## Copy/Paste Workflow

When a future package is safe for parallel launch, add it in this format:

# PARALLEL TASK WP-XXXX — Title

```text
Read:

collaboration/work_packages/pending/WP-XXXX_PARALLEL_title.md

and do exactly what it says.
```
