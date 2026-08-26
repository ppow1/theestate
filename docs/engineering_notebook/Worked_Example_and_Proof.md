# Worked Example and Proof

The isolated proof in `experiments/engineering_notebook_001/` uses a fixed
Markdown corpus and three stages: parser output, schema output, and populated
HTML. Each stage is executed by a separate Python process that receives only a
serialized verified packet, current-stage files, and current validation context.
No prior transcript or in-memory state is passed.

After each stage the harness atomically writes a revisioned state and receipt.
Session 2 creates a handoff; a deliberately conflicted state is rejected,
refreshed from authoritative facts, and session 3 resumes from the refreshed
handoff. The proof records process IDs, packet/state digests, acknowledgments,
actions, validation, proposals, receipts, handoffs, and fixture hashes. The
result is precisely **HARNESS-LEVEL FRESH-SESSION CONTINUITY**, not local-model
acceptance, resident integration, or institutional acceptance.
