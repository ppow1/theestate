# MHTML Runtime-Canon Recovery Implementation

Status: implementation evidence; non-canonical; no recovered conversation body is stored here.

## Proven defect

Browser-saved ChatGPT MHTML contains role-bearing message elements whose HTML nesting is not reliable enough for `div`-depth message termination. The authoritative five-archive calibration set preserves 102 rendered messages and 25 assistant messages, including complete WP-4111 and WP-4112 bodies in `tab4.mhtml`.

## Required source changes

1. End one message immediately before the next `data-message-author-role` element, or at EOF.
2. Scan every `text/html` MIME representation and deduplicate identical recovered messages.
3. Detect multiple bounded runtime-canon candidates per assistant message.
4. Recognize a WP title and runtime-canon subtitle on separate lines.
5. Prefer matching explicit canon closure as the end boundary.
6. Preserve all recovered material as non-canonical review evidence; never promote automatically.

## Mandatory acceptance gates

- Five archives inventoried.
- Seven HTML MIME representations scanned.
- 102 total messages recovered.
- 25 assistant messages recovered.
- WP-4111 recovered from message `bb605e81-9828-4e36-a536-eb0339053adb` with matching explicit closure.
- WP-4112 recovered from message `6a46eb57-8e36-474a-ae7e-05a7be6e5b90` with matching explicit closure.
- Large quoted WP-0026 startup seed rejected as authored canon.
- Two clean reruns produce byte-identical reports.
- No private MHTML archive or recovered canon body is committed.

## Delivery patches

The implementation was developed as two ordered patches:

1. Repair stdlib message boundaries and reconcile all MIME HTML representations.
2. Add multi-candidate runtime-canon segmentation with explicit closure evidence.

These patches were validated outside the repository against the preserved source archives. They must be applied to a branch and exercised by the focused ingestion/recovery tests plus the private real-archive acceptance harness before merge.
