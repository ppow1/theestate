# Command Chair Macro Controller Discussion Summary

Date: 2026-07-07
Classification: Estate Internal
Status: Discussion captured / pending hardware evaluation
Related area: Command Chair, Estate Peripheral Service, physical control surface

## Purpose

This summary captures the discussion about adding programmable macro controllers to Pat's chair-mounted workstation / Command Chair.

The conversation began as a search for a small programmable keyboard or macropad, but the design direction matured into a possible first physical Estate console node: a small input/output peripheral that can accept button and encoder input while also providing visible status feedback through RGB and/or an LCD display.

## Working Context

The workstation is chair-mounted, not rack-mounted. The existing full-size hinged keyboard works, but deploying it creates commitment friction: once it is folded down, Pat is more likely to remain seated. The design goal is therefore not only typing comfort, but reducing activation energy and preserving movement.

The Command Chair should support quick entry, quick exit, and low-friction interaction without making Pat feel mechanically trapped.

## Key Design Insight

The macropad should not be treated only as an input device.

It should be evaluated as a possible Estate peripheral:

- Input: keys, encoder turns, encoder presses.
- Output: RGB status, RGB notifications, LCD mode text, visual attention cues.
- Integration: Stream Deck mode selection, Window Swapper control, KVM/window control, and future Estate notifications.

The major shift was recognizing that RGB is not cosmetic. If it can be controlled or at least meaningfully configured, it can act as a local notifier. The Estate could flash or color a key/LED to signal that something needs attention.

Examples discussed:

- Blue pulse: mail or message waiting.
- Red flash: failure or urgent Estate attention.
- Green: normal/idle.
- Purple: AI worker completed.
- Yellow: review pending.

Pressing the illuminated key could eventually acknowledge the notification and open the relevant Estate surface.

## Desired Hardware Capabilities

The ideal long-term device would have:

- QMK, VIA, or Vial support where possible.
- At least one rotary encoder.
- Preferably three encoders for independent continuous controls.
- Programmable keys.
- Controllable RGB, ideally per-key addressable RGB.
- Wired USB operation.
- On-device memory for mappings.
- A simple physical shape suitable for chair mounting.
- Optional LCD display for current mode text such as EST, WIN, OBS, CAD, or MAIL.

The key tradeoff identified was that small, cheap, Amazon-available devices rarely also provide QMK/VIA/Vial. The market seems to split between generic proprietary macropads and better open-firmware enthusiast boards that are harder to source quickly.

## Candidate Hardware Discussed

### Pabile P9

The Pabile P9 was the strongest open-firmware candidate found during the search. It advertised RP2040, QMK, Vial-compatible firmware, hot-swappable MX sockets, USB-C, per-key RGB, layers, macros, tap dance, combos, assembly guidance, and enclosure files.

The preferred variant was the assembled 3D casing plus 3 encoders version.

Concern: availability and shipping cost. Several desirable 3-encoder variants appeared sold out or difficult to obtain.

### Generic 3-key / 1-knob Amazon units

Several inexpensive Amazon units were considered as rapid experiments. These are not likely to be long-term Estate console hardware, but they can teach whether a physical encoder becomes part of Pat's muscle memory.

Concern: most use proprietary software and do not advertise QMK/VIA/Vial.

### Koolertron 9-key / 2-knob controller

Pat ordered this as a practical first larger test unit.

Known or claimed properties from listing / product summary:

- 9 keys.
- 2 programmable knobs.
- LED backlit.
- PC/Mac programming software.
- USB connection.
- Settings saved on the device MCU.
- Can map keys and knobs to keystrokes, macros, multimedia functions, or combinations.

This device is a prototype surface for learning whether more keys and multiple knobs are useful in the Command Chair.

### AI-KSEN 3-key wired custom keyboard with LCD

Pat also ordered the AI-KSEN 3-key wired custom keyboard with LCD screen from Alibaba.

Important qualities:

- 3 keys.
- 1 encoder.
- 0.96 inch LCD display.
- RGB around the control surface.
- Manufacturer listing, low cost, order protection.

The LCD changes the design question. Even if the device is not QMK/VIA, the LCD may make it valuable as a mode-confirming peripheral, for example displaying EST, MAIL, WIN, OBS, CAD, or AI depending on the current Stream Deck-selected context.

Concern: dynamic software control of the LCD and RGB is unknown.

## Orders Placed

### Amazon Order

- Order number: 112-7837769-4031422
- Order date: 2026-07-07
- Total: USD 31.30
- Expected arrival: arriving tomorrow from the order screenshot
- Item: Koolertron 9-Key Mechanical Numpad with 2 Programmable Knobs, LED Backlit Macro Gaming Keyboard, Fully Customizable Numeric Keypad for PC

### Alibaba Order

- Order number: 306886991001023631
- Order date: 2026-07-07 PDT
- Total: USD 21.01
- Seller: Shenzhen Ai-Ksen Technology Co., Ltd.
- Guaranteed delivery: 2026-07-15 to 2026-07-25
- Item: AI-KSEN 3-Key Wired Custom Keyboard LCD Color Screen Display Game Keyboard DIY Accessories
- Product listing: https://www.alibaba.com/product-detail/AI-KSEN-3-Key-Wired-Custom_1601663545705.html
- Alibaba product ID: 1601663545705

## Proposed Software Architecture

Do not bind Estate logic directly to one hardware vendor.

Define a stable Estate Peripheral abstraction first, then write adapters for each physical device.

Possible interface shape:

```text
Estate Peripheral Service

Inputs:
- OnButtonPressed(device_id, button_id)
- OnEncoderTurned(device_id, encoder_id, delta)
- OnEncoderPressed(device_id, encoder_id)

Outputs:
- SetIndicator(device_id, indicator_id, color)
- FlashIndicator(device_id, indicator_id, color, pattern)
- SetModeLabel(device_id, text)
- ClearNotification(device_id, indicator_id)
```

The first implementation may be AutoHotkey, Python, vendor configuration software, Stream Deck profiles, or a hybrid. The abstraction should survive replacement of the hardware.

## Proposed Stream Deck Role

The Stream Deck should likely act as the dynamic mode selector.

Examples:

- Stream Deck page: Browser -> encoder scrolls.
- Stream Deck page: CAD -> encoder zooms.
- Stream Deck page: Estate -> encoder navigates Estate surfaces.
- Stream Deck page: OBS -> encoder controls audio or scene-related parameters.

The macropad remains tactile and stable. The Stream Deck provides mode context and dynamic labels.

## Open Questions

- Can the ordered Koolertron RGB be controlled dynamically, or only configured statically?
- Can the AI-KSEN LCD be updated dynamically after configuration?
- Can the AI-KSEN RGB be controlled dynamically?
- Do either devices expose enough HID behavior to support a clean software adapter?
- Does Pat actually use one encoder constantly, or are multiple encoders necessary?
- Is the best final form one encoder plus more buttons, or three encoders plus fewer buttons?
- Where should the devices physically mount on the Command Chair?

## Current Decision

Proceed with imperfect prototype hardware rather than continuing to search for the perfect controller.

The two ordered devices will provide practical information:

- Koolertron tests a larger control surface with more buttons and two knobs.
- AI-KSEN tests a small mode-aware LCD controller with one encoder and three keys.

The final controller can evolve after real chair use, software inspection, and physical mounting tests.
