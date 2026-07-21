# Runtime Canon Recovery Workflow Retrigger

This branch-local marker exists only to generate a pull-request synchronize event after the temporary recovery workflow on `main` was corrected to interpret the reviewed apply-patch artifact.

Final synchronize trigger issued after the workflow was updated to listen for both `edited` and `synchronize` events.

It must be removed before PR #437 is considered merge-ready.
