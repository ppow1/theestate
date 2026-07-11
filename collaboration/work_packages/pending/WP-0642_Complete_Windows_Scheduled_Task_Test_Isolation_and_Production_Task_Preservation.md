# WP-0642 - Complete Windows Scheduled Task Test Isolation and Production Task Preservation

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-10

## Mission

Complete the Windows Scheduled Task test-isolation repair after live acceptance proved that WP-0641 did not fully protect the production task.

The full runtime regression suite passed 27 of 27 tests, but the production Scheduled Task `Estate Operations Runtime Host` was deleted during the suite. The remaining defect is in test isolation, not in runtime-host PID