# WP-0653 Live Acceptance Report

Environment: Linux CI/container implementation environment for `ppow1/theestate` branch `wp-0653-governed-publication`.

Live Windows target acceptance was not executed in this container because the Windows Estate target and GitHub `origin` credentials are not configured here. The controller now records this class of condition as a bounded publication/policy blocker instead of declaring readiness.

Local acceptance evidence completed:

- focused git-backed integration tests create a bare upstream, let the existing controller commit the Activation Ledger, publish without a manual Steward `git push`, fetch, verify `origin/main` contains the authored commit by ancestry, and verify `main...origin/main` is `0 0` with a clean checkout;
- unauthorized publication leaves the local controller-authored commit ahead of upstream and blocks readiness;
- recovery publishes a generic attributable controller-authored ahead commit without hard-coding any commit SHA;
- production policy tests block missing policy and trivial compile-only / zero-duration observation defaults;
- explicit non-applicable gate rationale permits repository-only targets without automatic institutional acceptance.

Remaining blocker for full live Windows acceptance: run this branch on the configured Windows Estate target with configured upstream credentials and the canonical target metadata populated.
