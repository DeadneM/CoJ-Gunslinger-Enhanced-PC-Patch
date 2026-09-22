# Technical notes - Steam v45 / GOG v45

This document records the retained implementation details for the current validated game payloads and the active unified distribution architecture.

Current version designation:

`v2Pv45Sv45G`

- patcher generation: **v2P**
- Steam payload: **v45S**
- GOG payload: **v45G**

Steam v45 and GOG v45 intentionally reuse the already validated Build 44 gameplay payloads for their respective editions. The v45 milestone changed distribution only.

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

The Hold Quick Reload gate uses:

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

## Payload lineage

### Steam

The validated Steam v45 target is byte-identical to the validated Steam Build 44 gameplay payload.

- `CoJGunslinger.exe`: `125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844`
- `Data0.pak`: `55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744`

The installer supports two exact Steam source pairs:

1. original retail Steam;
2. Enhanced PC Patch Build 15.

Both now go directly to the same validated Steam v45 target through independent COJDP1 deltas.

### GOG

The validated GOG v45 target is byte-identical to the validated GOG PE2 Build 44 test payload.

- `CoJGunslinger.exe`: `c0cc2bcb760e5b6fff9e6f0ab5e4ccf3acec5859f08f11a77339f551501a45e4`
- `Data0.pak`: `601fdb9311635352af663b7c10959b263f5650a463f4dc20f1b54b390273d62b`

The validated GOG port keeps the original GOG entry point and platform integration. Steam's `.bind` / DRM code is not copied.

The GOG executable lacks the Steam `.bind` virtual-address range used by the common validated `.mod` payload. The port reserves that range with an inert zero-filled padding section and keeps `.mod` at its established RVA. This avoids relocating the validated hooks while adding no Steam code.

The original Steam and GOG `Data0.pak` archives both contain 1774 entries. Their local records differ in only four GOG-specific menu resources:

- `data/menu/scr/menumissionend.xui`
- `data/menu/scr/menumain.xui`
- `data/menu/scr/menuingame.xui`
- `data/menu/scr/menuarcade.xui`

None belongs to the 19-resource gameplay patch set. The validated GOG target preserves those four GOG-specific resources byte-for-byte.

## Active installer architecture: COJDP1

The active patcher no longer reconstructs Build 15 and Build 44 in stages at runtime.

It embeds six compressed direct-delta streams:

- Steam retail EXE -> Steam v45 EXE
- Steam retail Data0 -> Steam v45 Data0
- Steam Build 15 EXE -> Steam v45 EXE
- Steam Build 15 Data0 -> Steam v45 Data0
- GOG retail EXE -> GOG v45 EXE
- GOG retail Data0 -> GOG v45 Data0

Each decompressed stream begins with the `COJDP1` magic and stores:

- expected source size;
- expected target size;
- expected source SHA-256;
- expected target SHA-256;
- instruction count;
- copy/literal reconstruction instructions.

Supported operations are deliberately small:

- opcode `0`: copy a verified range from the source;
- opcode `1`: append literal bytes carried by the delta.

The reader rejects:

- an invalid magic;
- a source size/hash mismatch;
- truncated instructions or literals;
- copy ranges outside the source;
- unknown opcodes;
- unexpected trailing patch data;
- a target size/hash mismatch.

The installer additionally verifies the complete edition-specific target before staging and again after installation.

## Historical reconstruction lineage

The older reconstruction work is retained under `legacy/` for auditability and for rebuilding the project history, but it is **not part of the active installer path**.

Historically:

- the Steam retail archive was reconstructed to Build 15 with a semantic Data0 recipe;
- Build 44 then applied a small EXE delta and Data0 overlay;
- the Data0 lineage preserved 1774 entries, copying 1755 unchanged local ZIP records byte-for-byte and rebuilding 19 modified resources;
- raw DEFLATE, ZipCrypto, local headers, data descriptors and central-directory metadata were reproduced deterministically.

Those historical assets remain valuable documentation, but the current installer bypasses that staged chain by applying verified direct deltas to the final v45 targets.

## Retired GOG CJPG1 experiment

The earlier GOG `CJPG1` reconstruction path is retired.

The old artifact produced parser/decompression failures during installer validation and was found to be malformed/truncated. It is preserved only in:

`legacy/gog-cjpg1/`

It must not be used by current builds or release workflows.

An intermediate standalone GOG COJDP1 probe is likewise preserved under:

`legacy/gog-direct-probe/`

The authoritative active payload is the embedded direct-delta set in the current installer source.

## Versioning

The installer version and game payload versions are independent.

Format:

`v<PATCHER>Pv<STEAM>Sv<GOG>G`

Current designation:

`v2Pv45Sv45G`

This allows future installer-only changes to increment `P` without falsely changing the Steam or GOG gameplay payload version.
