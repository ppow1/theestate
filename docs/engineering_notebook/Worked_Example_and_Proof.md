# Worked Example and Proof

The isolated proof in `experiments/engineering_notebook_001/` uses a fixed
Markdown corpus and three stages: parser output, schema output, and populated
HTML. Each stage is executed by a new bounded `WorkerSession` that receives only
the verified packet and current-stage files. The prior transcript is not passed.

After each stage the harness updates task/evidence/continuity facts and records
the next stage. A changed fixture digest is detected as `conflicted`, and the
execution gate rejects it. The proof is intentionally a deterministic worker
protocol test, not a claim that a coding model was onboarded or accepted.
