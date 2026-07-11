# Disaster-Recovery Rehearsal

1. Create a full backup with all nine resident-runtime coverage areas.
2. Verify the backup manifest against copied files.
3. Restore into an empty isolated test root.
4. Recompute restored checksums against the manifest.
5. Report `ok=false` if verification, restore, collision handling, or checksum
   comparison fails; include all failures instead of hiding partial results.
