# Runtime-Canon Segmentation Acceptance Results

## Preserved archive baseline

- HTML representations: 7
- Rendered messages: 102
- Assistant messages: 25

## Detector results

- Qualified title/canon candidates: 3
- Substantive candidates: 2
- Rejected quoted/startup seed: 1

## Calibration fixtures

### WP-4111

- Archive: `tab4.mhtml`
- Message ID: `bb605e81-9828-4e36-a536-eb0339053adb`
- Start boundary: 0
- End boundary: 38,930
- Explicit matching closure: yes
- Substantive: yes

### WP-4112

- Archive: `tab4.mhtml`
- Message ID: `6a46eb57-8e36-474a-ae7e-05a7be6e5b90`
- Start boundary: 0
- End boundary: 41,606
- Explicit matching closure: yes
- Substantive: yes

### Negative fixture

- Identifier: `WP-0026`
- Archive: `tab3.mhtml`
- Message ID: `96f3d88c-649c-4ab4-949d-451a160862c0`
- Rejected because the body is a quoted/startup seed.

## Safety

The segmenter only identifies and bounds review candidates. It does not promote, overwrite, or modify pending work-package definitions.
