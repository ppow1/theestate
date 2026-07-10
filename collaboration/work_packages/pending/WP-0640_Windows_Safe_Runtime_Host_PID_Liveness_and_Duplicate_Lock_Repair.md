# WP-0640 - Windows-Safe Runtime Host PID Liveness and Duplicate-Lock Repair

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-10

## Mission

Repair the Windows runtime-host liveness and duplicate-lock path exposed by live validation of WP-0639.

The Estate Operations Runtime Host must reject a second active lock immediately, recover only genuinely