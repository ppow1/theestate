# WP-0644 - Eliminate Real Windows Task Scheduler Access From Manifest-Only Host Tests

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-11

## Mission

Repair the remaining Windows test-isolation defect in `tests/test_operations_runtime_host.py` so manifest-only host tests cannot create, replace, query, or delete any