# Rollback Plan

Stop the WP-4228 CLI, archive and verify the JSONL chain, remove its configured store/index, and revert the production module/CLI registration. No source-domain record is rewritten, so existing dashboard, Grace, Helen, Engineering lifecycle, Dispatch, and staged artifacts continue unchanged. Verify inspection against the archive and run affected regressions.
