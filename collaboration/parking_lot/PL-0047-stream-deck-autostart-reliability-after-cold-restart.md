# PL-0047 — Stream Deck Autostart Reliability After Cold Restart

Status: Captured
Priority: High
Category: Stream Deck / Startup Reliability
Originator: Pat / Steward
Date Captured: 2026-08-11
Target Milestone: After current Codex Desk cold-start acceptance work

## Idea

Investigate why Elgato Stream Deck did not automatically start after a real cold restart even though startup behavior had recently been configured through Stream Deck settings and an additional Windows startup mechanism.

The immediate operational workaround is manual launch. Do not interrupt current work to investigate this now.

## Why It Is Parked

The failure was discovered immediately after a cold restart while other acceptance work was already in progress. Pat explicitly does not want to spend time on Stream Deck startup diagnosis during the current session.

## Investigation Scope When Promoted

Determine the authoritative startup path and why it failed after reboot. Inspect only when this item is intentionally promoted, including as applicable:

- Stream Deck's own start-with-Windows setting;
- Startup-folder registration;
- Task Scheduler or other Windows startup registration previously added;
- whether duplicate/conflicting startup mechanisms exist;
- user-session timing or dependency ordering after login;
- whether the process starts and exits, never starts, or is blocked before UI initialization;
- evidence from a real cold restart rather than warm process restart alone.

Prefer one authoritative, reliable startup mechanism instead of accumulating additional redundant launch paths.

## Acceptance Condition

After an actual Windows cold restart and login, Stream Deck starts without manual intervention, loads the expected Estate profiles/plugin surface, and remains running long enough for normal Operator Deck use.

## Explicit Non-Action

Do not investigate, repair, add another scheduler/startup entry, or modify the Stream Deck plugin merely because this item has been captured. Patricia is manually starting Stream Deck for the current session and returning to the already-active work.
