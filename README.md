# CoJ-Gunslinger-Enhanced-PC-Patch

Deterministic source reconstruction for the **Call of Juarez: Gunslinger Enhanced PC Patch**.

The repository now preserves two validated milestones:

- **Build 15** - stable public baseline, reconstructed directly from the unmodified Steam files.
- **Build 44** - current validated development build, reconstructed deterministically from exact Build 15.

This repository does **not** require separately redistributing the retail `CoJGunslinger.exe` or `Data0.pak`.

## Build 44

Build 44 carries the validated Build 42 startup CPU fix, the centered 48-XUI reload-prompt spacing, and the validated controller Hold Quick Reload implementation.

See `BUILD44_NOTES.md` for the technical audit and exact native hook locations.

### Reconstruct Build 44

Python 3.8+ only. No third-party packages are required.

First reconstruct exact Build 15 from the retail Steam files:

```bash
python patcher.py --game-dir "PATH_TO_RETAIL_FILES"
```

Then upgrade that exact reconstruction to Build 44:

```bash
python patcher_build44.py --build15-dir build15 --output-dir build44
```

The Build 44 upgrader verifies its Build 15 inputs before changing anything and verifies the final Build 44 hashes before writing the result.

Expected Build 44 outputs:

- `CoJGunslinger.exe`
  - size: `23203840`
  - SHA-256: `125a3b088e502049913d7a6d20f0ad76d7a0e5fe086d14bb257c4d0798ca5844`
- `Data0.pak`
  - size: `9350117`
  - SHA-256: `55cab794160a244ef3db3abfa0e3beb23643ebb20c3d95831d0c553905372744`

The reconstruction was compared byte-for-byte against the validated Build 44 files.

## Build 15 reproducibility

Both Build 15 files are reproducible from the retail originals:

- `CoJGunslinger.exe` - deterministic CJPD1 binary delta
- `Data0.pak` - semantic reconstruction of the 19 modified resources, while copying all 1755 unchanged ZIP records byte-for-byte from the retail archive

The Data0 builder reproduces the archive layout, raw DEFLATE streams, PKZIP ZipCrypto encryption, local headers, data descriptors, central directory and offsets.

The resulting files were compared against the validated Build 15 references with full binary comparison, not hashes alone.

## Required retail files

Place the original Steam files in one directory under their normal names:

- `CoJGunslinger.exe`
- `Data0.pak`

Expected retail SHA-256 values:

- `CoJGunslinger.exe`: `ca1c4766900feb867372e0e2e87eb5adb92ca26ee537598a034ed7be1313d93c`
- `Data0.pak`: `0debd38c1560830486d8f7bdecf3806324e4f6357f1353ea0058b47bdfe8aa3b`

## Reconstruct Build 15

```bash
python patcher.py --game-dir "PATH_TO_RETAIL_FILES"
```

The rebuilt files are written to `./build15/` by default.

To patch the verified retail files in place:

```bash
python patcher.py --game-dir "PATH_TO_RETAIL_FILES" --in-place
```

Expected Build 15 outputs:

- `CoJGunslinger.exe`
  - size: `23203840`
  - SHA-256: `b468197ddcba6547db8dda2efc3cd29f524f57992756aa813142b5531b2fd78d`
- `Data0.pak`
  - size: `9350103`
  - SHA-256: `ffa18821657e8f25063897a28730a03fb962abf22d572fb3d4fdd83772db0eab`

## Source layout

- `patcher.py` - deterministic retail -> Build 15 reconstruction
- `patcher_build44.py` - deterministic Build 15 -> Build 44 reconstruction
- `HASHES.json` - retail and Build 15 integrity manifest
- `HASHES_BUILD44.json` - Build 44 integrity manifest
- `patches/verified/CoJGunslinger.build15.cjpd` - Build 15 EXE delta
- `patches/verified/CoJGunslinger.build44_from_build15.cjpd.b64` - compact Build 44 EXE overlay
- `data0/recipes_*.json` - readable Build 15 Data0 transformations
- `data0/metadata_*.json` - Build 15 ZIP/DEFLATE/ZipCrypto metadata
- `build44/data0_overlay.json` - semantic HUD overlay and archive metadata for Build 44
- `BUILD44_NOTES.md` - validated Build 44 technical notes
- `VERIFY_REPORT.txt` - Build 15 byte-for-byte verification record

The retail game files are intentionally excluded from this repository.
