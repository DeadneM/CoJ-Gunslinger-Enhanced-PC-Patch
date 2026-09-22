# Technical notes - cumulative Build 45

This document records the retained implementation details for the current cumulative build. Build 45 adds unified Steam + GOG distribution without changing the validated gameplay payloads from their Build 44 references. Rejected diagnostic branches are intentionally omitted.

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


## GOG port

The validated GOG port keeps the original GOG entry point and platform integration. Steam's `.bind` / DRM code is not copied.

The GOG executable lacks the Steam `.bind` virtual-address range used by the common validated `.mod` payload. The port therefore reserves that range with an inert zero-filled padding section and keeps `.mod` at its established RVA. This avoids relocating the validated hooks while adding no Steam code.

The original Steam and GOG `Data0.pak` archives both contain 1774 entries. Their local records differ in only four GOG-specific menu resources:

- `data/menu/scr/menumissionend.xui`
- `data/menu/scr/menumain.xui`
- `data/menu/scr/menuingame.xui`
- `data/menu/scr/menuarcade.xui`

None is part of the 19-resource patch set, so the common semantic reconstruction leaves them byte-for-byte GOG while rebuilding the common modified resources.

## Build 45 integrity

Steam target:
- `CoJGunslinger.exe`: `125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844`
- `Data0.pak`: `55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744`

GOG target:
- `CoJGunslinger.exe`: `c0cc2bcb760e5b6fff9e6f0ab5e4ccf3acec5859f08f11a77339f551501a45e4`
- `Data0.pak`: `601fdb9311635352af663b7c10959b263f5650a463f4dc20f1b54b390273d62b`

Build 45 intentionally reuses the already validated Build 44 gameplay payload for each edition. Its change is the unified, edition-aware distribution/reconstruction layer.
