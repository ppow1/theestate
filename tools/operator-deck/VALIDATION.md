# Operator Deck Maiden Voyage Validation Receipt

Status: workstation validated  
Date: 2026-07-21  
Classification: Estate Internal  
Branch: `work/operator-deck-maiden-voyage`

## Validated environment

- Windows 11 workstation
- Four 3840 × 2160 displays at 175% effective scaling
- Stream Deck XL, 32 keys
- Estate Status Bridge plugin `com.estate.statusbridge`
- AutoHotkey v2
- PowerShell 7 and Windows PowerShell 5.1

## Validated capabilities

1. Voice Typing state detection:
   - Windows Client CBS microphone record active -> `listening`, high confidence.
   - Record inactive -> `off`, high confidence.
   - Continuous transitions `OFF -> LISTENING -> OFF` observed.
2. Device-neutral state:
   - Unified publisher reported dictation, selection, and binding validity.
   - Selection armed/unarmed and dictation transitions were observed continuously.
3. Monitor layout:
   - Four displays and work areas discovered.
   - Primary-display 84-pixel taskbar exclusion preserved.
   - All four quadrants on the primary display validated.
4. Window identity and movement:
   - Exact binding distinguished one of six same-title ChatGPT Chrome windows.
   - Bound target placement across monitors validated.
   - Two-step select/place validated.
   - Context-sensitive quadrant source/destination placement validated.
   - Quadrant-origin selection published `source_slot: M1_BOTTOM_RIGHT` for the valid bound Chrome window.
5. Recovery:
   - Single-window movement undo validated.
   - Two-window swap and transactional undo validated.
6. Stream Deck:
   - Guarded patch preflight passed.
   - Timestamped backup created at `A:\AI\Tools\EstateStreamDeckPlugin\backups\operator-deck-voice-20260721-220737`.
   - Source and installed JS/manifests matched after patch.
   - Node and JSON validation passed.
   - Manifest action count increased from 18 to 19.
   - `com.estate.statusbridge.operator_deck.dictation` registered visibly.
   - Key rendered `VOICE / OFF`.
   - Physical tap activated Voice Typing.
   - Key rendered green `VOICE / ON` while listening.
7. Stream Deck quadrant installation:
   - Guarded 19-to-35-action preflight passed without writes.
   - Timestamped backup created at `A:\AI\Tools\EstateStreamDeckPlugin\backups\operator-deck-quadrants-20260721-224645`.
   - Sixteen quadrant action UUIDs installed.
   - Source and installed JS/manifests matched after patch.
   - Node and JSON validation passed.
   - Stream Deck profile layout was not modified automatically.

## Important distinctions

- Operator Deck monitor IDs are spatial: M1 upper-left, M2 upper-right, M3 lower-left primary, M4 lower-right.
- Named bindings identify exact windows; temporary selection identifies the next window movement.
- Chrome window titles may change with active tabs; validated HWND/PID identity remains authoritative.
- An idle-but-visible Voice Typing toolbar currently reports `off`; only microphone listening reports `listening`.
- Raw workstation reports and screenshots remain local/private and are not repository artifacts.

## Remaining review boundary

No branch merge, repository promotion, automatic profile injection, or broad Stream Deck profile redesign has occurred. Further physical-key expansion should preserve existing action UUIDs and the established gesture engine.
