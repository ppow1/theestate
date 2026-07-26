# Command Chair HID Integration Checkpoint

Date: 2026-07-26  
Estate Change: EC-000095  
Classification: Estate Internal; backup bundle contains Restricted historical input macros  
Status: Three controller families validated; AI-KSEN LCKEY/LCD paused pending official software

## Purpose

This checkpoint preserves the verified hardware identities, mappings, tools, failures, recovery artifacts, and next steps from the Command Chair HID integration work. It is the resume point for future Operator Deck work and is intended to prevent rediscovery when the AI-KSEN three-button LCD controller is revisited.

## Current Result

The following input surfaces are operationally validated:

1. Two matching white three-button/one-encoder controllers.
2. One E9s nine-key/two-encoder controller.
3. One UtechSmart Venus Pro mouse using a dedicated second onboard profile.

The AI-KSEN LCKEY three-button/one-encoder/LCD controller is identified and inspected, but its keys, encoder, RGB, and LCD have not been reprogrammed because its proprietary configuration protocol differs from the generic `1189:8890` macropad protocol.

## Namespace Allocation

| Device | Trigger namespace | Validation |
| --- | --- | --- |
| White LEFT controller | `F13` through `F18` | Verified by Raw Input |
| White RIGHT controller | `F19` through `F24` | Verified by Raw Input |
| E9s grid and upper encoder | `LCtrl+F13` through `LCtrl+F24` | Verified |
| E9s lower encoder | `LAlt+F22` through `LAlt+F24` | Verified |
| Venus Pro profile 2 | `Ctrl+Shift+F1` through `Ctrl+Shift+F12` | All twelve buttons verified |
| AI-KSEN LCKEY | `Shift+F13` through `Shift+F18` reserved only | Not provisioned |

These namespaces are intentionally distinct. Future Operator Deck bindings should consume the stable trigger namespace instead of binding Estate logic directly to a vendor-specific device path.

## Device 1 and Device 2: Matching White Controllers

### Identity

- VID/PID: `VID_1189&PID_8890`
- No usable serial number.
- Each controller exposes multiple keyboard, mouse, consumer-control, and vendor-defined HID interfaces.
- Interface 1 uses usage page `0xFF00`, usage `0x0001` as the configuration channel.
- Identical VID/PID means role identity depends on the Windows container ID and fixed USB-port discipline.

### Durable role identities

LEFT:

```text
ContainerId: {E963B22C-F4D2-794D-9783-EA3F040F00F0}
```

RIGHT:

```text
ContainerId: {7B5BC6C0-8859-11F1-A778-CC474004B334}
```

These container IDs may change if Windows re-enumerates the hardware. Fixed physical USB ports remain part of the identity strategy.

### Verified LEFT mapping

| Control | Trigger |
| --- | --- |
| Button 1 | `F13` |
| Button 2 | `F14` |
| Button 3 | `F15` |
| Encoder clockwise | `F16` |
| Encoder press | `F17` |
| Encoder counterclockwise | `F18` |

### Verified RIGHT mapping

| Control | Trigger |
| --- | --- |
| Button 1 | `F19` |
| Button 2 | `F20` |
| Button 3 | `F21` |
| Encoder clockwise | `F22` |
| Encoder press | `F23` |
| Encoder counterclockwise | `F24` |

The RIGHT encoder direction was explicitly corrected after capture proved the first direction assignment was reversed.

### Tooling and local evidence

Local working directory:

```text
A:\theestate\tools\operator-deck
```

Known local artifacts:

```text
runtime\command-chair-controller-map.json
runtime\command-chair-hid-baseline.json
runtime\command-chair-hid-paired-controllers.json
Test-CommandChairRawInput.ps1
Provision-CommandChairController.py
vendor\macropad-open-source
```

Python `hidapi` 0.15.0 was installed during discovery. The open-source provisioning source successfully programmed these two generic controllers.

## Device 3: E9s Nine-Key/Two-Encoder Controller

### Identity

- VID/PID: `VID_A286&PID_1DAD`
- Manufacturer: `MYKB`
- Product: `E9s`
- Serial: `vial:f64c2b3c`
- Firmware/configuration family: Vial/QMK
- Configuration interface: interface 1, usage page `0xFF60`, usage `0x0061`

### Verified mapping

Grid keys:

| Physical key | Trigger |
| --- | --- |
| 1 | `LCtrl+F13` |
| 2 | `LCtrl+F14` |
| 3 | `LCtrl+F15` |
| 4 | `LCtrl+F16` |
| 5 | `LCtrl+F17` |
| 6 | `LCtrl+F18` |
| 7 | `LCtrl+F19` |
| 8 | `LCtrl+F20` |
| 9 | `LCtrl+F21` |

Upper encoder:

| Control | Trigger |
| --- | --- |
| Clockwise | `LCtrl+F22` |
| Press | `LCtrl+F23` |
| Counterclockwise | `LCtrl+F24` |

Lower encoder:

| Control | Trigger |
| --- | --- |
| Clockwise | `LAlt+F22` |
| Press | `LAlt+F23` |
| Counterclockwise | `LAlt+F24` |

The direction order was captured and verified with clockwise first and counterclockwise second.

### RGB

Vial exposes Backlight/RGB controls for the E9s. Static and firmware-supported RGB behavior is available through Vial. Dynamic Estate-controlled notification behavior remains a future adapter task and has not been proven.

### Backup

The exact factory Vial backup is stored in the repository backup bundle as:

```text
E9s-factory-backup.vil
```

SHA-256:

```text
caf22135f827faa0a23e8df74aabd093281da8313c926c1e0adf0bcd213f4459
```

## Device 4: AI-KSEN LCKEY Three-Key/Encoder/LCD

### Product identity

- Product: AI-KSEN 3-Key Wired Custom Keyboard LCD Color Screen Display Game Keyboard DIY Accessories
- Alibaba product ID: `1601663545705`
- Canonical listing: `https://www.alibaba.com/product-detail/AI-KSEN-3-Key-Wired-Custom_1601663545705.html`
- Alibaba order: `306886991001023631`
- Seller: Shenzhen Ai-Ksen Technology Co., Ltd.
- Seller confirmed: no QMK, VIA, or Vial support.
- Seller was asked for the official Windows configuration software, manual, key/encoder programming documentation, RGB documentation, LCD documentation, and MCU identity.

### HID identity

- VID/PID: `VID_1189&PID_8890`
- Manufacturer: `Lctech`
- Product: `LCKEY`
- No serial.

Interfaces:

| Interface | Usage page | Usage | Purpose |
| --- | --- | --- | --- |
| MI_00 | `0x0001` | `0x0006` | Keyboard |
| MI_01 | `0xFF00` | `0x0001` | Vendor configuration channel |
| MI_03 | `0x0001` | `0x0002` | Mouse |
| MI_04 | `0x000C` | `0x0001` | Consumer control |

### Observed factory behavior

| Control | Factory output |
| --- | --- |
| Button 1 | `Ctrl+A` |
| Button 2 | `Ctrl+C` |
| Button 3 | `Ctrl+V` |
| Encoder press | Bare Left Ctrl |
| Encoder rotation | No keyboard event observed |

### Critical failed approach

The generic macropad protocol used successfully on the white `1189:8890` controllers was tested against the LCKEY configuration channel.

The dry run produced plausible generic packets, but an actual attempt did not change the LCKEY behavior. Verification showed that the original factory outputs remained intact. This proves that sharing VID/PID and usage-page values does not prove protocol compatibility.

Do not repeat generic provisioning writes against the LCKEY.

### Candidate alternative

`kriomant/ch57x-keyboard-tool` was identified as a possible mature configuration path for certain `1189:8890` devices and three-key-plus-knob layouts. On Windows it requires the USBdk low-level driver. It has not been validated against this LCD firmware and should not be used until the official seller software or firmware details are evaluated.

### Reserved mapping

If the official configuration method becomes available, the provisional namespace is:

| Control | Reserved trigger |
| --- | --- |
| Button 1 | `Shift+F13` |
| Button 2 | `Shift+F14` |
| Button 3 | `Shift+F15` |
| Encoder clockwise | `Shift+F16` |
| Encoder press | `Shift+F17` |
| Encoder counterclockwise | `Shift+F18` |

This is a reservation, not a completed mapping.

### Resume procedure

1. Check the Alibaba seller response for the official software, manual, firmware, or MCU details.
2. Preserve any official software package and documentation before installing it.
3. Back up the device configuration with the official tool if possible.
4. Determine whether LCD and RGB updates are persistent configuration only or dynamically controllable.
5. Capture read-only protocol traffic before sending new writes.
6. Reconcile physical direction labels using clockwise/counterclockwise language.
7. Provision one control at a time and verify it through Raw Input.
8. Do not reuse the generic white-controller provisioning protocol without new evidence.

## Device 5: UtechSmart Venus Pro RGB Wireless MMO Mouse

### Identity

- Model family: UtechSmart Venus Pro RGB MMO Wireless Gaming Mouse
- Official model: `US-D16000-WGM`
- VID/PID: `VID_25A7&PID_FA07`
- Bus description: `2.4G Wireless Receiver`
- Installed software: Venus Wireless Gaming Mouse 3.1
- Publisher: UtechSmart
- Install path: `C:\Program Files (x86)\UtechSmart\Venus wireless\`
- Main executable: `OemDrv.exe`

The Redragon K585 tray application is unrelated to the mouse.

### Onboard profile behavior

The mouse has exactly two confirmed onboard profiles selected using the physical underside profile button.

- Profile 1: Pat's established daily workflow and muscle-memory mappings.
- Profile 2: Command Chair trigger surface and possible authorization keypad.

Profile 1 was preserved. It contains historical macros including obsolete credentials and must be treated as Restricted even though those credentials have since been changed.

### Verified Profile 2 mapping

| Mouse button | Trigger |
| --- | --- |
| 1 | `Ctrl+Shift+F1` |
| 2 | `Ctrl+Shift+F2` |
| 3 | `Ctrl+Shift+F3` |
| 4 | `Ctrl+Shift+F4` |
| 5 | `Ctrl+Shift+F5` |
| 6 | `Ctrl+Shift+F6` |
| 7 | `Ctrl+Shift+F7` |
| 8 | `Ctrl+Shift+F8` |
| 9 | `Ctrl+Shift+F9` |
| 10 | `Ctrl+Shift+F10` |
| 11 | `Ctrl+Shift+F11` |
| 12 | `Ctrl+Shift+F12` |
| 13 | Existing `Fire key`, unchanged |
| 14 | Left mouse button, unchanged |
| 15 | Middle mouse button, unchanged |
| 16 | Right mouse button, unchanged |

All twelve Command Chair triggers were captured successfully in sequence.

### UtechSmart format findings

- Exported configuration uses a `.profile` suffix.
- The import file picker filters for `.jmk`.
- An identical binary copy renamed to `.jmk` imports successfully.
- The file is 11,332 bytes.
- The active assignment bank begins at offset `0x260`.
- Assignment records are 40 bytes each.
- The combination record uses type byte `0xA1`.
- Modifier byte `0x03` represents Ctrl+Shift in this format.
- HID usage codes `0x70` through `0x7B` represent F1 through F12.
- Controlled Step1/Step2 comparison changed only the expected assignment bytes.
- No changing file-level checksum was observed.
- The generated complete `.profile` and importer-compatible `.jmk` are byte-identical.

The software rejected F13 through F24 in the key-combination field. The mouse therefore uses `Ctrl+Shift+F1` through `Ctrl+Shift+F12`.

### Authorization concept

Profile 2 can also act as a contextual authorization keypad:

1. Switch physically to profile 2.
2. Enter a sequence using the twelve thumb buttons.
3. Operator Deck consumes the trigger sequence without typing a credential into an application.
4. A valid sequence temporarily unlocks protected local actions.
5. Timeout, clear, submit failure, or profile change clears the pending sequence.

This must not store or emit an actual password, API key, or reusable credential. It is a local authorization gesture and possible additional factor, not a standalone security boundary.

## HID Collision Findings

The paired-controller baseline changed from 92 HID devices with one white controller to 101 with both connected. Both matching controllers share VID/PID but enumerate under distinct container IDs.

The E9s added nine interfaces under `VID_A286&PID_1DAD`.

The LCKEY added eight visible controller interfaces under `VID_1189&PID_8890`.

The mouse exposes ten interfaces under `VID_25A7&PID_FA07`.

Multiple interfaces from one physical composite HID device are normal and must not be mistaken for multiple physical devices. Collision handling should use VID/PID, container identity, interface path, serial when available, and fixed USB-port policy.

## Backup Bundle

Repository bundle:

```text
tools/operator-deck/command-chair/backups/command-chair-backups-2026-07-26.json
```

Restore script:

```text
tools/operator-deck/command-chair/Restore-CommandChairBackupBundle.ps1
```

The bundle contains:

| File | Purpose |
| --- | --- |
| `E9s-factory-backup.vil` | Factory Vial backup |
| `VenusPro-Pre-CommandChair-2026-07-26.profile` | Original customized mouse profile |
| `VenusPro-CC-Step1.profile` | Controlled F1 comparison state |
| `VenusPro-CC-Step2.profile` | Controlled F2 comparison state |
| `VenusPro-CommandChair-Complete.profile` | Completed mapping with export suffix |
| `VenusPro-CommandChair-Complete.jmk` | Byte-identical importer-compatible copy |

The restore script decodes each payload and verifies its SHA-256 hash.

## Local Runtime State

These files were created on Pat's workstation and remain local runtime evidence:

```text
A:\theestate\tools\operator-deck\runtime\command-chair-controller-map.json
A:\theestate\tools\operator-deck\runtime\command-chair-hid-baseline.json
A:\theestate\tools\operator-deck\runtime\command-chair-hid-paired-controllers.json
A:\theestate\tools\operator-deck\runtime\command-chair-hid-auxiliary-3.json
A:\theestate\tools\operator-deck\runtime\command-chair-e9s-hid-interfaces.json
A:\theestate\tools\operator-deck\runtime\command-chair-hid-lcd-controller.json
A:\theestate\tools\operator-deck\runtime\command-chair-lckey-hid-interfaces.json
A:\theestate\tools\operator-deck\runtime\venuspro-commandchair-test.log
```

Runtime observations should remain under `runtime/`; this checkpoint preserves the stable conclusions and recovery payloads.

## Next Implementation Step

Build an Operator Deck input bridge that:

1. Consumes the stable trigger namespaces.
2. Maps physical inputs to configurable logical actions.
3. Preserves device-independent action names.
4. Supports mode/context changes from Stream Deck or Operator Deck state.
5. Adds the optional temporary authorization-sequence state machine.
6. Leaves vendor configuration software out of the normal runtime path.

Do not begin the LCKEY write path until official configuration evidence is available.
