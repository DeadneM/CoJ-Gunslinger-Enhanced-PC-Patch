# Build 44 notes

Build 44 is the current validated development build of the Enhanced PC Patch.

It is reconstructed **on top of exact Build 15**, so the original Build 15 source reconstruction remains preserved and independently reproducible.

## Validated changes after Build 15

### Startup CPU fix

Build 42 isolated the high-CPU startup state to the empty Win32 message-queue path.

The engine loop performs `PeekMessageA`; when the queue is empty, it immediately updates and loops again. The validated fix redirects only the empty-queue branch through a `Sleep(1)` helper.

- empty-queue conditional branch: `0x00401F04`
- helper: `0x033A4E00`
- delay: `Sleep(1)`

XInput and the VfW/AVI path were tested separately and did not change the CPU behavior. They are left vanilla in the validated branch.

### Reload prompt

The normal `[R] RECHARGER` prompt keeps the native centering calculation.

The dedicated native spacing constant is now **48.0 XUI** at `0x033A4960`. Both the total-width calculation and second-element placement use the same constant, so increasing the gap does not introduce a manual center offset.

No manual `T_Key` / `T_Text` position hack is used in the validated layout.

### Hold Quick Reload on controller

Build 44 adds controller Hold Quick Reload without adding another XInput poll.

The native controller mapper already converts `XINPUT_GAMEPAD_X (0x4000)` to internal input ID `0x15` / Reload:

- mapper boolean: around `0x0066B2F0`
- Reload ID assignment hook: `0x0066B2FA`
- gamepad held latch: `0x033A4964`
- capture helper: `0x033A4970`
- combined held-state helper: `0x033A4990`
- existing keyboard Reload latch: `0x033A4898`

The Hold Quick Reload gate therefore uses:

`KeyboardReloadHeld OR NativeGamepadReloadHeld`

No extra `XInputGetState`, no controller-slot scan, and no `inputs_pad.scr` remapping are required.

## Rejected diagnostic builds

Builds 37-41 were diagnostics and are **not** bases for Build 44.

- 37/38: rejected XInput capture experiment; crash
- 39: rejected direct XInput bypass; ABI/stack-cleanup error
- 40: corrected XInput diagnostic; CPU unchanged
- 41: VfW decompression diagnostic; CPU unchanged
- 43: first controller-held capture point had no effect

Build 44 branches from validated Build 42, not from those rejected experiments.

## Integrity

Validated Build 44:

- `CoJGunslinger.exe`: `125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844`
- `Data0.pak`: `55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744`
- `COJ_Gunslinger_44.zip`: `2f2360a7859c80c0b9cfa93d0959f5da4ad69d4a0921afb75c9d3e0ce30551b5`

The repository reconstruction was tested byte-for-byte against the validated Build 44 EXE and Data0.
