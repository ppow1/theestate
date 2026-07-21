# WP-4125 Implementation Report

## Delivery

The runtime canon, evidence/result schemas, deterministic runner, estate separation checks, revision packet, fixtures, and tests are implemented. The baseline run covers all eight catalog residents and honestly reports `review_required`: no commissioned portrait pixels or completed Steward comparison boards exist in the repository.

## Validation claim

Implemented checks cover category/angle presence, IDs and resident bindings, source/asset paths and SHA-256, workflow provenance, duplicate bytes, declared visual-fingerprint convergence, review audit fields, external advisory-score boundaries, diagnostics, promotion gates, and remediation output. No computer vision, facial recognition, landmark detection, or visual similarity is claimed.

## Outstanding human evidence

Every resident still requires generated assets, comparison boards, unlabeled resident grid, native 32/64 previews, applicable controlled cross-model evidence, and named/dated Steward decisions for every governed visual check. Therefore no resident is eligible for canonical promotion and the overall validation remains review-required rather than visually complete.

## Commands

- `PYTHONPATH=src python -m estate.portraits.consistency data/portraits/validation/wp4125_estate_validation_input.json --output reports/visual_campaign_02/WP-4125_VALIDATION_REPORT.json --root .`
- `pytest -q tests/test_wp4125_portrait_consistency.py`
