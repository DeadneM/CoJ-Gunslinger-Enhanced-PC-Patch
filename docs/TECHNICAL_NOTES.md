# Technical notes - validated Build 44

This document records the retained implementation details for the current cumulative build. Rejected diagnostic branches are intentionally omitted from the public source overview.

## Startup CPU fix

The startup CPU issue was isolated to the empty Win32 message-queue path.

The engine calls `PeekMessageA`. When no message is available, the original code immediately continues the update loop. The validated patch redirects only that existing empty-queue conditional branch through a `Sleep(1)` helper.

- empty-queue conditional branch: `0x00401F04`
- helper: `0x033A4E00`
- delay: `Sleep(1)`

The conditional semantics are preserved. The delay is not inserted into Present, XInput, video decoding, or unrelated worker paths.

## Reload prompt

The normal reload prompt keeps the engine's native centering calculation.

- dedicated spacing constant: `0x033A4960`
- validated spacing: **48.0 XUI**

Both native gap calculations reference the same constant, preserving centering without manual child-position offsets.

## Controller Hold Quick Reload

The implementation reuses the game's native controller mapping instead of adding another XInput poll.

The native mapper converts `XINPUT_GAMEPAD_X (0x4000)` to internal input ID `0x15` / Reload.

- Reload ID assignment hook: `0x0066B2FA`
- gamepad held latch: `0x033A4964`
- capture helper: `0x033A4970`
- combined held-state helper: `0x033A4990`
- existing keyboard Reload latch: `0x033A4898`

The Hold Quick Reload gate uses the logical combination:

`KeyboardReloadHeld OR NativeGamepadReloadHeld`

No extra `XInputGetState` poll, controller-slot scan, or `inputs_pad.scr` remapping is required.

## Combo / Upgraded visibility

The retained implementation preserves the vanilla gate and filters only the relevant Combo/Upgraded call site.

- vanilla `B1D0F0` gate remains intact;
- filtering is limited to `B1B562 -> B1BD60`;
- runtime `FloatingScoreVis` / mode state is used instead of globally hiding the parent HUD.

This keeps unrelated HUD behavior, duel presentation and audio paths intact.

## Arcade score HUD

The Arcade score-HUD visibility fix is isolated to its own wrapper in the patch section. It does not reuse the Combo/Upgraded visual gate.

## Data0 reconstruction

The Build 15 reconstruction keeps the archive at **1774 entries**.

- 1755 unchanged local ZIP records are copied byte-for-byte from the retail archive.
- 19 modified resources are reconstructed from the stored recipes.
- raw DEFLATE, ZipCrypto, local headers, data descriptors, central-directory metadata and offsets are reproduced deterministically.

Build 44 then applies the current semantic overlay on top of the verified Build 15 archive.

## Integrity

Validated Build 44:

- `CoJGunslinger.exe`: `125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844`
- `Data0.pak`: `55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744`

The reconstruction chain verifies exact SHA-256 values before accepting output.
