# Call of Juarez: Gunslinger - Enhanced PC Patch

Source repository for the **Enhanced PC Patch** for the Steam version of *Call of Juarez: Gunslinger*.

The project is distributed as a cumulative patch. The current validated target is **Build 44**. The Windows patcher reconstructs that build from verified game files and never redistributes the original game executable or archive.

## What the patch improves

The cumulative patch includes the validated work from all retained builds, including:

- enhanced draw distance, LOD and high-end graphics settings;
- native horizontal FOV range extended to **80-120**, with **100** as the default when no explicit value is configured;
- improved keyboard controls and remappable weapon switching;
- Weapon Trick and weapon drop/throw keyboard support;
- Developer Menu access and related UI fixes;
- Auto Reload / Manual Reload improvements and Hold Quick Reload;
- controller Hold Quick Reload support;
- HUD layout and scaling corrections;
- centered reload prompt with corrected native spacing;
- surgical Combo / Upgraded-card visibility handling;
- Arcade score-HUD visibility handling;
- startup high-CPU fix using the engine's empty Win32 message-queue path;
- Steam integration and the supported ULC entitlements remain intact.

The patch intentionally preserves unrelated game behavior instead of applying broad global hooks.

## Installation

The public Nexus Mods package contains the Windows patcher.

1. Place `COJ_Gunslinger_Patcher.exe` next to `CoJGunslinger.exe` in the game directory.
2. Run the patcher.
3. It locates `coj4/Data0.pak`, verifies the input files, creates backups, reconstructs the current validated build, verifies the result, and installs it.

The patcher accepts:

- the exact original Steam files;
- the exact Build 15 pair used by the deterministic reconstruction chain;
- Build 44 itself, which is detected as already installed.

Unknown or mixed files are rejected **before modification**.

## Safety and source review

The Windows patcher is built from the source in this repository with PyInstaller.

It:

- contains no retail game executable or `Data0.pak`;
- does not download game files;
- does not require network access;
- does not install a service or driver;
- does not request administrator privileges itself;
- modifies only the verified local game files;
- creates `.Backup` copies before installation;
- builds and verifies the new pair before replacement;
- restores the previous pair if replacement fails;
- verifies the installed Build 44 hashes one final time.

Because the tool patches an executable and a game archive, automated malware scanners may treat the packaged patcher conservatively. The complete reconstruction source and build workflow are provided here for review.

## Patcher versioning

Patcher versions follow the same cumulative integer build number as the mod.

For Build 44:

- GitHub Release tag: `v44`
- release asset: `COJ_Gunslinger_Patcher_Build44.exe`
- Windows file/product version: `Build 44`
- the console header reports `Latest cumulative build: 44`

The source-of-truth release number is `release/VERSION`. A release is published only when that file changes, so ordinary source/documentation commits do not create extra public releases.

## Validated Build 44 hashes

| File | SHA-256 |
| --- | --- |
| `CoJGunslinger.exe` | `125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844` |
| `Data0.pak` | `55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744` |

Original Steam inputs expected by the reconstruction:

| File | SHA-256 |
| --- | --- |
| `CoJGunslinger.exe` | `ca1c4766900feb867372e0e2e87eb5adb92ca26ee537598a034ed7be1313d93c` |
| `Data0.pak` | `0debd38c1560830486d8f7bdecf3806324e4f6357f1353ea0058b47bdfe8aa3b` |

## Build the Windows patcher from source

The reproducible Windows packaging workflow is in:

`.github/workflows/build-patcher.yml`

It uses Python 3.12 and PyInstaller and produces:

`COJ_Gunslinger_Patcher.exe`

The workflow includes the deterministic patch data and reconstruction metadata, but no proprietary retail game files.

To inspect the patcher logic, start with:

- `installer/COJ_Gunslinger_Patcher.py` - user-facing cumulative installer;
- `patcher.py` - deterministic Retail -> Build 15 reconstruction;
- `patcher_build44.py` - deterministic Build 15 -> Build 44 reconstruction.

## Deterministic reconstruction

Build 44 remains reproducible from the exact Steam originals in two verified stages.

### 1. Retail -> Build 15

```bash
python patcher.py --game-dir "PATH_TO_RETAIL_FILES"
```

Build 15 is an internal reproducibility milestone. The EXE is reconstructed with a compact CJPD1 delta. `Data0.pak` is reconstructed semantically while preserving unchanged archive records byte-for-byte.

### 2. Build 15 -> Build 44

```bash
python patcher_build44.py --build15-dir build15 --output-dir build44
```

Both stages verify their source and output hashes.

## Repository layout

```text
.github/workflows/          Windows patcher build workflow
installer/                  Standalone patcher source and build notes
patches/verified/           Compact verified EXE deltas
data0/                      Deterministic Data0 reconstruction recipes/metadata
build44/                    Current Data0 overlay
patcher.py                  Retail -> Build 15 reconstruction
patcher_build44.py          Build 15 -> Build 44 reconstruction
HASHES.json                 Retail / Build 15 integrity manifest
HASHES_BUILD44.json         Current Build 44 integrity manifest
docs/TECHNICAL_NOTES.md     Validated implementation notes
```

Packaged mod ZIPs and retail game files are intentionally **not stored in this repository**. Release archives are maintained separately for Nexus Mods.

## Technical notes

See `docs/TECHNICAL_NOTES.md` for the validated native hooks and reconstruction details.
