# Migration Plan

Migration is a non-destructive index: validate the identity map, hash original artifacts, attach canonical aliases, preserve paths and original hashes, and reject aliases with multiple matches. Historical staged files and decision records remain untouched. During rollout the existing dashboard remains available. The manifest is `migration_manifest.json`.
