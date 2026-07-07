# WP-2026-07-07 - Command Chair Macro Controller Integration

Status: open
Classification: Estate Internal
Requested by: Pat / Steward
Area: Command Chair, Estate Peripheral Service, workstation ergonomics
Related summary: docs/summaries/2026-07-07_command_chair_macro_controller_discussion.md

## Parking Lot Entry

Integrate the newly ordered macro controllers into the Command Chair after hardware arrives and is inspected.

This is intentionally parked until the devices are physically available. The hardware is not expected to be perfect. The purpose is to learn from real use and adapt.

## Hardware Ordered

Order identifiers, totals, and expected delivery windows are recorded in the related discussion summary rather than repeated here.

The two ordered devices are:

1. Koolertron 9-Key Mechanical Numpad with 2 Programmable Knobs, LED Backlit Macro Gaming Keyboard, Fully Customizable Numeric Keypad for PC.
2. AI-KSEN 3-Key Wired Custom Keyboard LCD Color Screen Display Game Keyboard DIY Accessories.

## Mission

Turn the two prototype macro controllers into usable Command Chair control surfaces and determine what the eventual Estate physical console should require.

The main goal is not to perfect the first hardware. The main goal is to discover which controls Pat actually uses in the chair and whether RGB/LCD output can become an Estate notification surface.

## Scope

Initial work should cover:

1. Inspect both devices after arrival.
2. Identify their configuration software, firmware behavior, and HID presentation.
3. Determine whether keys and encoders can be mapped reliably.
4. Determine whether RGB can be controlled dynamically or only configured statically.
5. Determine whether the AI-KSEN LCD can be updated dynamically or only configured during setup.
6. Create first-pass mappings for Window Swapper, Stream Deck modes, and common workstation actions.
7. Test where each device should physically mount on the Command Chair.
8. Decide whether either device should remain permanent or be treated only as a prototype.

## Boundaries

- Do not redesign the Estate to fit these devices.
- Do not create a new Estate office or department for hardware controls.
- Do not make one vendor's software the architectural foundation.
- Do not assume QMK/VIA/Vial support unless verified.

## Required Reading

- AI_START_HERE.md
- AI_HINTS.md
- docs/governance/Estate_Orientation_Handbook.md
- docs/governance/Estate_Manual.md
- docs/collaboration/Estate_Collaboration_Layer_v1.md
- docs/summaries/2026-07-07_command_chair_macro_controller_discussion.md

## Proposed Architecture

Create or design toward an Estate Peripheral Service abstraction rather than direct coupling to vendor software.

The future service should distinguish:

- Physical device adapters.
- Logical Estate actions.
- Input events from keys and encoders.
- Output events to RGB, LEDs, or LCD labels.
- Stream Deck selected mode.
- Window Swapper and KVM actions.

A first interface might include:

```text
OnButtonPressed(device_id, button_id)
OnEncoderTurned(device_id, encoder_id, delta)
OnEncoderPressed(device_id, encoder_id)
SetIndicator(device_id, indicator_id, color)
FlashIndicator(device_id, indicator_id, color, pattern)
SetModeLabel(device_id, text)
ClearNotification(device_id, indicator_id)
```

## Candidate First Mappings

### Koolertron

Use the 9 keys and 2 knobs to test tactile workstation controls:

- Window left / right / swap.
- KVM previous / next.
- Push-to-talk or mute.
- Scroll, volume, or zoom on knobs.
- Possible Stream Deck mode-dependent behavior.

### AI-KSEN

Use the LCD and single encoder to test mode-aware operation:

- LCD shows current mode: EST, WIN, OBS, CAD, MAIL, AI, or CHAT.
- Encoder controls the selected mode function.
- Three keys provide acknowledge / previous / next or mode-specific actions.
- RGB, if controllable, becomes an Estate attention indicator.

## Acceptance Criteria

This parking lot item can move forward when:

- Both devices have arrived or one is confirmed unusable.
- Configuration method is documented.
- HID behavior is understood.
- RGB/LCD control limits are known.
- A first-pass chair-mounted control layout is proposed.
- A decision is made about whether to build a software adapter, continue with vendor configuration only, or replace hardware with a QMK/Vial device.

## Notes

The key institutional insight from the discussion is that the physical control surface may become an Estate console node, not merely a macro pad. If RGB or LCD output can be controlled, the device can become a local notifier for Estate status and worker attention requests.
