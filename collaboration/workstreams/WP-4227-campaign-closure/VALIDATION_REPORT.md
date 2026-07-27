# WP-4227 validation report

## Results

| Area | Result | Evidence |
|---|---|---|
| Prerequisite merges | Pass | local merge history contains PRs #474–#481 relevant to WP-4220–WP-4226 |
| Layering/dependency direction | Pass | architecture map and closure static checks |
| Cyclic dependencies | Pass | no later campaign package imports from an earlier layer |
| Published-interface consumption | Pass | file/JSON boundaries and version checks; WP-4222's documented projection loader is the only direct provider load |
| Advisory authority | Pass | source scan plus existing behavioral tests |
| Schemas | Pass | 22 JSON documents parse and expose 22 unique, versioned `$id` values |
| CLI help/error surfaces | Pass | every campaign diagnostic entry point returns usable `--help` output |
| Deterministic replay | Pass | WP-4226 replay tests and complete focused campaign suite |
| Fixtures/examples | Pass | focused package tests load representative valid, malformed, stale, missing-provider, and incompatible-version cases |
| Documentation | Pass | reconciliation, architecture/dependency, validation, and receipt are present |

## Commands

The focused prerequisite run completed with **72 passed**. With closure checks included, the
campaign suite validates schema inventory, dependency direction, authority-sensitive imports,
CLI help, published examples, deterministic behavior, malformed inputs, and replay.

## Limitations

The repository has no Git remote configured. Consequently remote-main synchronization and push
could not be validated from this checkout. This is an environment limitation, not a campaign
implementation failure. No browser screenshot is applicable because this package makes no
perceptible web-application change.

