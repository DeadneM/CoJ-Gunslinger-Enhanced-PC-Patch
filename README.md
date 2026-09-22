# Call of Juarez: Gunslinger - Enhanced PC Patch

Source repository for the **Enhanced PC Patch** for *Call of Juarez: Gunslinger*.

The current cumulative release is **Build 45** and supports the verified **Steam and GOG** editions with one Windows patcher. The patcher identifies the edition by SHA-256 before modifying anything and preserves the platform-specific files and behavior of that edition.

> Build 45 is the unified Steam + GOG distribution milestone. The validated game payloads are binary-identical to their respective Build 44 references; no previously validated game-code fix was changed for this release.

## What the patch improves

The cumulative patch includes:

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
- startup high-CPU fix using the engine's empty Win32 message-queue path.

The patch intentionally preserves unrelated game behavior instead of applying broad global hooks.

### Platform preservation

**Steam** keeps its Steam integration and supported ULC entitlements.

**GOG** keeps the GOG executable entry point/platform integration and its GOG-specific menu resources. The GOG branch does not inject Steam DRM, Steam platform code or Steam-only menu navigation.

## Installation

1. Place `COJ_Gunslinger_Patcher_Build45.exe` next to `CoJGunslinger.exe` in the game directory.
2. Run the patcher.
3. It locates `coj4/Data0.pak` (or `Data0.pak` beside the EXE), hashes both files, detects Steam or GOG, creates backups, reconstructs the matching target, verifies it, and installs it.

Accepted sources:

- exact original Steam files;
- exact Steam Enhanced PC Patch Build 15 pair;
- exact original GOG files;
- the current validated Steam or GOG target, detected as already installed.

Unknown, modified or mixed edition pairs are rejected **before modification**.

## Safety and source review

The Windows patcher is built from this repository with PyInstaller.

It:

- contains no retail game executable or retail `Data0.pak`;
- does not download game files;
- does not require network access;
- does not install a service or driver;
- does not request administrator privileges itself;
- modifies only a recognized local game pair;
- creates `.Backup` copies before installation;
- reconstructs and verifies the new pair before replacement;
- keeps a temporary rollback pair during replacement;
- verifies the installed hashes one final time.

Because the tool patches an executable and a game archive, automated malware scanners may treat the packaged patcher conservatively. The complete reconstruction source and GitHub Actions build workflow are provided for review.

## Patcher versioning

Patcher versions follow the cumulative integer build number.

For the current release:

- GitHub Release tag: `v45`
- release asset: `COJ_Gunslinger_Patcher_Build45.exe`
- Windows file/product version: `Build 45`
- console header: `Latest cumulative build: 45 | Steam + GOG`

The source-of-truth release number is `release/VERSION`. Changing that file publishes a new release; ordinary source/documentation commits do not.

## Validated Build 45 hashes

### Steam

| File | Original Steam | Build 45 target |
| --- | --- | --- |
| `CoJGunslinger.exe` | `ca1c4766900feb867372e0e2e87eb5adb92ca26ee537598a034ed7be1313d93c` | `125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844` |
| `Data0.pak` | `0debd38c1560830486d8f7bdecf3806324e4f6357f1353ea0058b47bdfe8aa3b` | `55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744` |

### GOG

| File | Original GOG | Build 45 target |
| --- | --- | --- |
| `CoJGunslinger.exe` | `c061b0cd177c04e9ae30bdd5b8693caff2c2474b8f48f8d9c7e2bcd05f817708` | `c0cc2bcb760e5b6fff9e6f0ab5e4ccf3acec5859f08f11a77339f551501a45e4` |
| `Data0.pak` | `7c5b83bc26a703abe4a55d460b73d0248168d16e7b2998d0d6e8a45244a03e60` | `601fdb9311635352af663b7c10959b263f5650a463f4dc20f1b54b390273d62b` |

See `HASHES_BUILD45.json` for the machine-readable manifest.

## Reproducibility

The common Data0 reconstruction remains semantic and deterministic. The original Steam and GOG archives have the same 1774-entry layout. Their source local records differ in only four GOG-specific menu resources, none of which belongs to the 19-resource patch set. The common recipe therefore rebuilds the modified resources while leaving those four GOG records untouched.

The GOG executable uses its own compact verified delta in:

`gog/build44/CoJGunslinger.gog44.cjpgz.b64`

The validated GOG PE layout keeps the GOG entry point and platform integration. An inert zero-filled padding section reserves the address range absent without Steam's `.bind` section, allowing the common validated `.mod` payload to retain its established addresses without copying Steam DRM code.

## Repository layout

```text
.github/workflows/          Windows build and release workflows
installer/                  Unified Steam + GOG patcher source
patches/verified/           Verified Steam EXE deltas
gog/build44/                Verified GOG EXE reconstruction delta
data0/                      Common deterministic Data0 recipes/metadata
build44/                    Validated current Data0 overlay
patcher.py                  Retail -> internal Build 15 reconstruction
patcher_build44.py          Internal Build 15 -> validated payload
HASHES_BUILD45.json         Current Steam + GOG integrity manifest
docs/TECHNICAL_NOTES.md     Validated implementation notes
```

Packaged mod ZIPs and retail game files are intentionally **not stored in this repository**. Public binaries are published through GitHub Releases / Nexus Mods.

## Technical notes

See `docs/TECHNICAL_NOTES.md` for the retained native hooks and implementation details.
