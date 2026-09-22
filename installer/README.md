# Windows patcher

`COJ_Gunslinger_Patcher_44.exe` is the first standalone Windows installer for the cumulative Enhanced PC Patch.

## Current target

The patcher always targets the latest validated cumulative build. The current target is **Build 44**.

Supported input pairs:

- original Steam `CoJGunslinger.exe` + original Steam `Data0.pak`
- exact Enhanced PC Patch Build 15 pair
- Build 44 itself (detected as already installed)

Unknown or mixed files are refused before patching.

## Safety model

The patcher:

1. finds `CoJGunslinger.exe` next to itself and `Data0.pak` in either `coj4\\Data0.pak` or the same directory;
2. hashes both files before doing anything;
3. creates `.Backup` copies only after the input pair is recognized;
4. reconstructs Build 44 in a temporary directory;
5. verifies the exact validated Build 44 SHA-256 hashes before installation;
6. stages and verifies the new files again before replacing the originals;
7. verifies the installed files one final time.

Validated Build 44 hashes:

- EXE: `125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844`
- Data0: `55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744`

## Build

GitHub Actions builds the Windows executable with PyInstaller. The workflow is `.github/workflows/build-patcher.yml` and publishes `COJ_Gunslinger_Patcher_44.exe` as a workflow artifact.

This first implementation deliberately reuses the already verified deterministic Python reconstruction code. A later native implementation can replace the packaging layer without changing the patch data or final hashes.
